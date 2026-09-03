# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Real-time Lead Ads webhook.

Configure in the Meta app (Webhooks product → Page object → leadgen field):
  Callback URL:  https://<site>/api/method/crm.integrations.meta.webhook.handle
  Verify token:  CRM Meta Settings → Webhook Verify Token

GET  = Meta's verification handshake (hub.challenge echo).
POST = leadgen notifications. The payload does NOT carry the lead data — only
{leadgen_id, page_id, form_id, ...}; the lead is fetched from /{leadgen_id}
with the page token. The POST body is authenticated with X-Hub-Signature-256
(HMAC-SHA256 of the raw body with the app secret).
"""

import hashlib
import hmac
import json

import frappe
from werkzeug.wrappers import Response

from crm.integrations.meta.client import get_app_secret, get_settings
from crm.integrations.meta.leads import ingest_leadgen_entry
from crm.integrations.meta.relay import route_for, valid_relay_signature


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
	# either Meta itself, or our own hub forwarding a notification for a page
	# this site owns (one shared app has a single callback URL for every client)
	if not (
		_valid_signature(request.headers.get("X-Hub-Signature-256"), raw_body)
		or valid_relay_signature(request.headers.get("X-CRM-Relay-Signature"), raw_body)
	):
		return Response("invalid signature", status=403, mimetype="text/plain")

	try:
		payload = json.loads(raw_body)
	except ValueError:
		return Response("bad payload", status=400, mimetype="text/plain")

	if payload.get("object") == "page":
		for entry in payload.get("entry") or []:
			for change in entry.get("changes") or []:
				if change.get("field") != "leadgen":
					continue
				value = change.get("value") or {}
				site = route_for(value.get("page_id"))
				if site:
					# not our page: hand it to the client site that owns it
					frappe.enqueue(
						"crm.integrations.meta.relay.forward",
						queue="short",
						site=site,
						payload={"object": "page", "entry": [{"changes": [change]}]},
					)
					continue
				# process out-of-request: webhooks must return 200 fast, and Meta
				# retries on non-200 — the queue gives us retries-with-log instead
				frappe.enqueue(
					"crm.integrations.meta.leads.ingest_leadgen_entry",
					queue="short",
					leadgen_id=value.get("leadgen_id"),
					page_id=value.get("page_id"),
					form_id=value.get("form_id"),
					created_time=value.get("created_time"),
				)
	frappe.db.commit()
	return Response("ok", mimetype="text/plain")


def _valid_signature(header: str | None, raw_body: bytes) -> bool:
	secret = get_app_secret()
	if not secret or not header or not header.startswith("sha256="):
		return False
	expected = hmac.new(secret.encode(), raw_body, hashlib.sha256).hexdigest()
	return hmac.compare_digest(header.split("=", 1)[1], expected)


@frappe.whitelist(allow_guest=True)  # nosemgrep: guest-whitelisted-method
def data_deletion(signed_request: str | None = None):
	"""Meta Data Deletion Request callback (required for App Review).

	Meta POSTs signed_request = base64url(signature).base64url(payload); the
	signature is HMAC-SHA256 of the payload with the app secret. We store no
	Facebook-user personal data keyed by their FB identity (leads live as CRM
	records under the advertiser's own account), so we acknowledge with a
	confirmation code and a status URL as the spec requires.
	"""
	import base64

	def b64url_decode(value: str) -> bytes:
		return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))

	if not signed_request or "." not in signed_request:
		return Response("bad request", status=400, mimetype="text/plain")

	secret = get_app_secret()
	if not secret:
		return Response("not configured", status=400, mimetype="text/plain")

	encoded_sig, encoded_payload = signed_request.split(".", 1)
	expected = hmac.new(secret.encode(), encoded_payload.encode(), hashlib.sha256).digest()
	if not hmac.compare_digest(b64url_decode(encoded_sig), expected):
		return Response("invalid signature", status=403, mimetype="text/plain")

	try:
		payload = json.loads(b64url_decode(encoded_payload))
	except ValueError:
		return Response("bad payload", status=400, mimetype="text/plain")

	confirmation_code = frappe.generate_hash(length=16)
	frappe.log_error(
		f"Meta data deletion request for user_id={payload.get('user_id')} code={confirmation_code}",
		"Meta: data deletion request",
	)
	frappe.db.commit()
	status_url = frappe.utils.get_url(
		f"/api/method/crm.integrations.meta.webhook.deletion_status?code={confirmation_code}"
	)
	return Response(
		json.dumps({"url": status_url, "confirmation_code": confirmation_code}),
		mimetype="application/json",
	)


@frappe.whitelist(allow_guest=True)  # nosemgrep: guest-whitelisted-method
def deletion_status(code: str | None = None):
	return Response(json.dumps({"code": code or "", "status": "complete"}), mimetype="application/json")
