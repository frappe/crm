# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Google Calendar connection — one button, no credentials to paste.

Same shape as the Meta connection: the agency owns ONE Google Cloud project,
its credentials live in the bench config, and the OAuth redirect goes to the
hub (Google, like Meta, matches redirect URIs exactly and has no wildcards).
The hub relays the authorization code to the site named in the signed state,
which exchanges it and stores the refresh token for that user.

The token is written into the framework's own `Google Calendar` doctype, so the
existing calendar sync and the booking busy-check keep working untouched.

Config keys (common_site_config.json, shared by every site):
    google_client_id, google_client_secret
    meta_hub_url / meta_relay_secret are reused — one hub for everything.
"""

import base64
import hashlib
import hmac
import json
import time
from urllib.parse import quote, urlencode

import frappe
import requests
from frappe import _
from frappe.utils import get_url

CALLBACK_PATH = "/api/method/crm.integrations.google.oauth.callback"
AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
# full calendar access: the framework's sync both reads and writes events
SCOPES = ("https://www.googleapis.com/auth/calendar",)
STATE_TTL = 900
TIMEOUT = 30

MANAGER_ROLES = {"System Manager", "Sales Manager", "Sales User"}


def _check_user():
	if not MANAGER_ROLES & set(frappe.get_roles()):
		frappe.throw(_("You cannot connect a calendar"), frappe.PermissionError)


def client_id() -> str:
	return (
		frappe.conf.get("google_client_id")
		or frappe.db.get_single_value("Google Settings", "client_id")
		or ""
	)


def client_secret() -> str:
	if frappe.conf.get("google_client_secret"):
		return frappe.conf["google_client_secret"]
	try:
		return frappe.get_doc("Google Settings").get_password("client_secret", raise_exception=False) or ""
	except Exception:
		return ""


def is_managed() -> bool:
	"""Credentials come from the bench: the client never sees them."""
	return bool(frappe.conf.get("google_client_id") and frappe.conf.get("google_client_secret"))


def hub_url() -> str:
	from crm.integrations.meta.oauth import hub_url as meta_hub

	return meta_hub()


def redirect_uri() -> str:
	return (hub_url() + CALLBACK_PATH) if hub_url() else get_url(CALLBACK_PATH)


def _state_secret() -> str:
	return (
		frappe.conf.get("meta_relay_secret") or frappe.local.conf.get("encryption_key") or frappe.local.site
	)


def sign_state(payload: str) -> str:
	return hmac.new(_state_secret().encode(), payload.encode(), hashlib.sha256).hexdigest()[:24]


def make_state(site: str, calendar: str) -> str:
	payload = json.dumps({"t": int(time.time()), "site": site.rstrip("/"), "cal": calendar})
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


@frappe.whitelist()
def get_login_url() -> dict:
	"""Where to send the browser to connect this user's Google Calendar."""
	_check_user()
	if not client_id() or not client_secret():
		frappe.throw(_("Google is not configured yet — ask your provider"))

	calendar = ensure_calendar_record()
	params = {
		"client_id": client_id(),
		"redirect_uri": redirect_uri(),
		"response_type": "code",
		"scope": " ".join(SCOPES),
		# offline + consent: without both, Google returns no refresh token on a
		# second authorisation and the link dies at the first token expiry
		"access_type": "offline",
		"prompt": "consent",
		"include_granted_scopes": "true",
		"state": make_state(get_url().rstrip("/"), calendar),
	}
	return {"login_url": f"{AUTH_URL}?{urlencode(params)}", "calendar": calendar}


def ensure_calendar_record() -> str:
	"""One Google Calendar document per user, created on first connect."""
	name = frappe.db.get_value("Google Calendar", {"user": frappe.session.user})
	if name:
		return name
	doc = frappe.get_doc(
		{
			"doctype": "Google Calendar",
			"calendar_name": frappe.utils.get_fullname(frappe.session.user),
			"user": frappe.session.user,
			"enabled": 1,
		}
	)
	doc.insert(ignore_permissions=True)
	return doc.name


@frappe.whitelist(allow_guest=True, methods=["GET"])  # nosemgrep: guest-whitelisted-method
def callback(code: str | None = None, state: str | None = None, **kwargs):
	"""Google's redirect target.

	Guest-accessible because the hub receives it in the browser of a user logged
	into THEIR site. The signed state says where to go; the destination site
	still requires a real session before storing anything.
	"""
	parsed = parse_state(state)
	if parsed and (parsed.get("site") or "").rstrip("/") != get_url().rstrip("/"):
		_relay_to_site(parsed["site"], code, state, kwargs)
		return

	if not parsed:
		_redirect_back(error=_("Invalid or expired connection attempt"))
		return
	_check_user()
	if not code:
		_redirect_back(error=kwargs.get("error") or _("Connection was cancelled"))
		return

	try:
		tokens = exchange_code(code)
		store_tokens(parsed.get("cal"), tokens)
		frappe.db.commit()
		_redirect_back()
	except Exception as exc:
		frappe.log_error(frappe.get_traceback(), "Google Calendar: connection failed")
		_redirect_back(error=str(exc)[:200])


def exchange_code(code: str) -> dict:
	response = requests.post(
		TOKEN_URL,
		data={
			"code": code,
			"client_id": client_id(),
			"client_secret": client_secret(),
			"redirect_uri": redirect_uri(),
			"grant_type": "authorization_code",
		},
		timeout=TIMEOUT,
	)
	data = response.json() if response.text else {}
	if response.status_code >= 300 or not data.get("refresh_token"):
		raise ValueError(data.get("error_description") or data.get("error") or _("No refresh token returned"))
	return data


def store_tokens(calendar: str | None, tokens: dict) -> None:
	"""Write the refresh token where the framework's calendar sync expects it.

	`Google Settings` is filled from the bench config too: without client id and
	secret there, the framework cannot refresh the token later.
	"""
	if is_managed():
		settings = frappe.get_doc("Google Settings")
		changed = False
		if settings.client_id != client_id():
			settings.client_id = client_id()
			changed = True
		if not settings.get_password("client_secret", raise_exception=False):
			settings.client_secret = client_secret()
			changed = True
		if not settings.enable:
			settings.enable = 1
			changed = True
		if changed:
			settings.save(ignore_permissions=True)

	name = calendar or frappe.db.get_value("Google Calendar", {"user": frappe.session.user})
	if not name:
		name = ensure_calendar_record()
	doc = frappe.get_doc("Google Calendar", name)
	if doc.user != frappe.session.user:
		frappe.throw(_("This calendar belongs to another user"), frappe.PermissionError)
	doc.refresh_token = tokens["refresh_token"]
	doc.enabled = 1
	doc.save(ignore_permissions=True)


def _relay_to_site(site: str, code: str | None, state: str, kwargs: dict) -> None:
	params = {"state": state}
	if code:
		params["code"] = code
	if kwargs.get("error"):
		params["error"] = kwargs["error"]
	frappe.local.response["type"] = "redirect"
	frappe.local.response["location"] = f"{site.rstrip('/')}{CALLBACK_PATH}?{urlencode(params)}"


def _redirect_back(error: str | None = None) -> None:
	target = "/crm?settings=" + quote("Google Calendar")
	if error:
		target += f"&google_error={quote(error[:300])}"
	frappe.local.response["type"] = "redirect"
	frappe.local.response["location"] = target
