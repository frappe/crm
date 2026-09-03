# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""WhatsApp webhook — hub side.

WhatsApp webhooks are configured per APP, so every message of every client
lands on one callback: this one. The hub splits the payload per WhatsApp
Business account and forwards each entry to the CRM that owns it.

The forwarded body is re-signed with the **app secret**, producing a genuine
`X-Hub-Signature-256`: the receiving site's WhatsApp app then validates it
exactly as if Meta had called it directly, so nothing on the client side needs
to know the hub exists.

Configure in the Meta app (Webhooks → WhatsApp Business Account):
  Callback URL:  https://<hub>/api/method/crm.integrations.whatsapp.webhook.handle
  Verify token:  CRM Meta Settings → Webhook Verify Token (on the hub)
  Fields:        messages, account_update
"""

import hashlib
import hmac
import json

import frappe
import requests
from werkzeug.wrappers import Response

from crm.integrations.meta.client import get_app_secret, get_settings

TIMEOUT = 15
# frappe_whatsapp's own endpoint: it turns the payload into WhatsApp Message docs
DOWNSTREAM_PATH = "/api/method/frappe_whatsapp.utils.webhook.webhook"


@frappe.whitelist(allow_guest=True)  # nosemgrep: guest-whitelisted-method
def handle(**kwargs):
	if frappe.request.method == "GET":
		return _verify_subscription(frappe._dict(kwargs))
	return _receive(frappe.request)


def _verify_subscription(args):
	settings = get_settings()
	if (
		args.get("hub.mode") == "subscribe"
		and settings.webhook_verify_token
		and args.get("hub.verify_token") == settings.webhook_verify_token
	):
		return Response(args.get("hub.challenge") or "", mimetype="text/plain")
	return Response("verification failed", status=403, mimetype="text/plain")


def _receive(request):
	raw_body = request.get_data() or b""
	if not valid_signature(request.headers.get("X-Hub-Signature-256"), raw_body):
		return Response("invalid signature", status=403, mimetype="text/plain")

	try:
		payload = json.loads(raw_body)
	except ValueError:
		return Response("bad payload", status=400, mimetype="text/plain")

	if payload.get("object") == "whatsapp_business_account":
		for entry in payload.get("entry") or []:
			site = route_for(entry)
			if not site:
				continue
			frappe.enqueue(
				"crm.integrations.whatsapp.webhook.forward",
				queue="short",
				site=site,
				entry=entry,
			)
	frappe.db.commit()
	return Response("ok", mimetype="text/plain")


def valid_signature(header: str | None, raw_body: bytes) -> bool:
	secret = get_app_secret()
	if not secret or not header or not header.startswith("sha256="):
		return False
	expected = hmac.new(secret.encode(), raw_body, hashlib.sha256).hexdigest()
	return hmac.compare_digest(header.split("=", 1)[1], expected)


def route_for(entry: dict) -> str | None:
	"""Site that owns this entry — by WABA id, falling back to the phone number."""
	waba_id = entry.get("id")
	site = waba_id and frappe.db.get_value("Meta WhatsApp Route", waba_id, "site_url")
	if not site:
		for change in entry.get("changes") or []:
			metadata = (change.get("value") or {}).get("metadata") or {}
			phone_number_id = metadata.get("phone_number_id")
			if phone_number_id:
				site = frappe.db.get_value(
					"Meta WhatsApp Route", {"phone_number_id": phone_number_id}, "site_url"
				)
				if site:
					break
	if not site:
		return None
	return site.rstrip("/")


def forward(site: str, entry: dict) -> None:
	"""Deliver one account's notification to the CRM that owns it.

	Signed with the app secret so the destination validates it as a normal Meta
	delivery — the hub is invisible to the receiving app.
	"""
	secret = get_app_secret()
	if not secret:
		frappe.log_error("No Meta app secret configured", "WhatsApp relay: cannot sign")
		return
	body = json.dumps({"object": "whatsapp_business_account", "entry": [entry]}).encode()
	signature = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
	try:
		response = requests.post(
			f"{site}{DOWNSTREAM_PATH}",
			data=body,
			headers={"Content-Type": "application/json", "X-Hub-Signature-256": signature},
			timeout=TIMEOUT,
		)
		if response.status_code >= 300:
			raise ValueError(f"HTTP {response.status_code}: {response.text[:200]}")
	except Exception:
		frappe.log_error(frappe.get_traceback(), f"WhatsApp relay: forward to {site} failed")
		return
	if entry.get("id") and frappe.db.exists("Meta WhatsApp Route", entry["id"]):
		frappe.db.set_value(
			"Meta WhatsApp Route",
			entry["id"],
			"last_forwarded_at",
			frappe.utils.now_datetime(),
			update_modified=False,
		)
