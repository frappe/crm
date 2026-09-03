# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""WhatsApp Embedded Signup — hub side.

Embedded Signup runs in the browser through Facebook's JS SDK, so the page that
hosts it must be listed in the app's *Allowed domains*. With one Frappe site per
client that list could never be complete, so the page lives on the hub
(`/whatsapp-connect`) and the client site only sends the user there with a
signed state saying who it is.

The code the flow returns lives for **30 seconds**, which is too tight to bounce
through the browser: the hub exchanges it for the business token itself and
hands the result to the client site server-to-server, signed with the relay
secret.

Meta reference: Embedded Signup v4 (v2 is retired on 15 October 2026).
"""

import base64
import hashlib
import hmac
import json
import time

import frappe
import requests
from frappe import _
from frappe.utils import get_url

from crm.integrations.meta.client import MetaAPIError, get_app_id, get_app_secret, graph_get, graph_post
from crm.integrations.meta.relay import relay_secret, sign
from crm.integrations.meta.relay import sign as relay_sign

CONNECT_PATH = "/whatsapp-connect"
STATE_TTL = 900
TIMEOUT = 30


def config_id() -> str:
	"""Facebook Login for Business configuration for Embedded Signup v4."""
	return frappe.conf.get("whatsapp_signup_config_id") or ""


def _state_secret() -> str:
	return relay_secret() or frappe.local.conf.get("encryption_key") or frappe.local.site


def sign_state(payload: str) -> str:
	return hmac.new(_state_secret().encode(), payload.encode(), hashlib.sha256).hexdigest()[:24]


def make_state(site: str) -> str:
	payload = json.dumps({"t": int(time.time()), "site": site.rstrip("/")})
	return f"{base64.urlsafe_b64encode(payload.encode()).decode()}.{sign_state(payload)}"


def parse_state(state: str | None) -> dict | None:
	if not state or "." not in state:
		return None
	try:
		encoded, signature = state.rsplit(".", 1)
		payload = base64.urlsafe_b64decode(encoded.encode()).decode()
		if not hmac.compare_digest(signature, sign_state(payload)):
			return None
		parsed = json.loads(payload)
	except Exception:
		return None
	if int(time.time()) - int(parsed.get("t") or 0) > STATE_TTL:
		return None
	return parsed


def allowed_site(site: str) -> bool:
	"""Same closed list the page routing uses: only our own sites may connect."""
	allowed = frappe.conf.get("meta_relay_sites")
	if not allowed:
		return True
	return site.rstrip("/") in [s.rstrip("/") for s in allowed]


OUTCOME_BY_EVENT = {
	"FINISH": "Completed",
	"FINISH_ONLY_WABA": "Completed",
	"FINISH_WHATSAPP_BUSINESS_APP_ONBOARDING": "Completed",
	"CANCEL": "Cancelled",
	"ERROR": "Error",
}


@frappe.whitelist(allow_guest=True, methods=["POST"])  # nosemgrep: guest-whitelisted-method
def log_session_event(state: str, event: str, data: str | dict | None = None) -> dict:
	"""Session logging — Meta requires Embedded Signup to be implemented with it.

	The hub page reports every step the business customer goes through, so an
	onboarding that stalls or is abandoned can actually be supported instead of
	guessed at. Nothing here is trusted: the state carries the signature, and
	only the fields we know are stored.
	"""
	parsed = parse_state(state)
	if not parsed:
		return {"ok": False}
	if isinstance(data, str):
		try:
			data = json.loads(data)
		except ValueError:
			data = {"raw": data[:500]}
	data = data or {}

	frappe.get_doc(
		{
			"doctype": "WhatsApp Signup Session",
			"site_url": parsed["site"],
			"event": (event or "")[:140],
			"current_step": (data.get("current_step") or "")[:140],
			"waba_id": data.get("waba_id") or "",
			"phone_number_id": data.get("phone_number_id") or "",
			"outcome": OUTCOME_BY_EVENT.get(event, "In Progress"),
			"details": json.dumps(data)[:5000],
		}
	).insert(ignore_permissions=True)
	frappe.db.commit()
	return {"ok": True}


@frappe.whitelist(allow_guest=True, methods=["POST"])  # nosemgrep: guest-whitelisted-method
def complete_signup(state: str, code: str, waba_id: str, phone_number_id: str) -> dict:
	"""Called by the hub page as soon as Embedded Signup finishes.

	Guest-accessible because the browser session belongs to the client site, not
	to the hub; the signed state is what authenticates the request.
	"""
	parsed = parse_state(state)
	if not parsed:
		frappe.throw(_("This connection attempt is invalid or has expired, please retry"))
	site = parsed["site"]
	if not allowed_site(site):
		frappe.log_error(f"WhatsApp signup from unlisted site {site}", "WhatsApp: signup refused")
		frappe.throw(_("This site is not allowed to connect WhatsApp"))

	token = exchange_code(code)
	number = describe_number(phone_number_id, token)

	claim_route(waba_id, phone_number_id, number.get("display_phone_number"), site)
	subscribe_waba(waba_id, token)
	deliver_to_site(site, token, waba_id, phone_number_id, number)

	log_session_event(
		state,
		"CONNECTED",
		{"waba_id": waba_id, "phone_number_id": phone_number_id, "current_step": "delivered"},
	)
	return {"ok": True, "site": site}


def exchange_code(code: str) -> str:
	"""Trade the 30-second Embedded Signup code for the business token."""
	try:
		data = graph_get(
			"oauth/access_token",
			token="",
			params={
				"client_id": get_app_id(),
				"client_secret": get_app_secret(),
				"code": code,
			},
		)
	except MetaAPIError as exc:
		frappe.throw(_("Meta refused the WhatsApp connection: {0}").format(exc))
	if not data.get("access_token"):
		frappe.throw(_("Meta did not return an access token"))
	return data["access_token"]


def describe_number(phone_number_id: str, token: str) -> dict:
	try:
		return graph_get(
			phone_number_id,
			token,
			{"fields": "display_phone_number,verified_name,quality_rating,platform_type"},
		)
	except MetaAPIError:
		frappe.log_error(frappe.get_traceback(), "WhatsApp: could not read the phone number")
		return {}


def subscribe_waba(waba_id: str, token: str) -> None:
	"""Subscribe the app to this WhatsApp Business account's webhooks.

	Coexistence needs more than `messages`: without `smb_message_echoes` the CRM
	never sees what the business writes from its phone, and without `history` the
	past conversations are never imported.
	"""
	try:
		graph_post(f"{waba_id}/subscribed_apps", token, {})
	except MetaAPIError:
		frappe.log_error(frappe.get_traceback(), f"WhatsApp: could not subscribe WABA {waba_id}")


def claim_route(waba_id: str, phone_number_id: str, display_number: str | None, site: str) -> None:
	"""Record which site owns this account, so the hub can route its messages.

	Like page routes, an account already owned by another site is never silently
	reassigned: the attempt is refused and logged.
	"""
	site = site.rstrip("/")
	current = frappe.db.get_value("Meta WhatsApp Route", waba_id, "site_url")
	if current and current.rstrip("/") != site:
		frappe.log_error(
			f"WABA {waba_id} is routed to {current}; {site} tried to take it over",
			"WhatsApp relay: takeover refused",
		)
		frappe.throw(_("This WhatsApp account is already connected to another site"))
	if current:
		frappe.db.set_value(
			"Meta WhatsApp Route",
			waba_id,
			{"phone_number_id": phone_number_id, "display_phone_number": display_number or ""},
		)
	else:
		frappe.get_doc(
			{
				"doctype": "Meta WhatsApp Route",
				"waba_id": waba_id,
				"phone_number_id": phone_number_id,
				"display_phone_number": display_number or "",
				"site_url": site,
			}
		).insert(ignore_permissions=True)
	frappe.db.commit()


def deliver_to_site(site: str, token: str, waba_id: str, phone_number_id: str, number: dict) -> None:
	"""Hand the credentials to the client CRM, signed with the relay secret."""
	if not relay_secret():
		frappe.throw(_("meta_relay_secret is not configured on this hub"))
	body = json.dumps(
		{
			"token": token,
			"waba_id": waba_id,
			"phone_number_id": phone_number_id,
			"display_phone_number": number.get("display_phone_number") or "",
			"verified_name": number.get("verified_name") or "",
		}
	).encode()
	try:
		response = requests.post(
			f"{site.rstrip('/')}/api/method/crm.integrations.whatsapp.api.receive_connection",
			data=body,
			headers={"Content-Type": "application/json", "X-CRM-Relay-Signature": relay_sign(body)},
			timeout=TIMEOUT,
		)
		if response.status_code >= 300:
			raise ValueError(f"HTTP {response.status_code}: {response.text[:200]}")
	except Exception as exc:
		frappe.log_error(frappe.get_traceback(), f"WhatsApp: handing the connection to {site} failed")
		frappe.throw(_("Could not hand the connection to your CRM: {0}").format(str(exc)[:200]))


__all__ = ["complete_signup", "config_id", "make_state", "parse_state", "sign"]
