import hmac
import json
from hashlib import sha256

import frappe


def build_signature(payload: dict, secret: str) -> str:
	body = json.dumps(payload, separators=(",", ":"), sort_keys=True)
	return hmac.new(secret.encode(), body.encode(), sha256).hexdigest()


def push_credit_status(payload: dict, event_id: str) -> None:
	settings = frappe.get_single("AnTek Integration Settings")
	if not settings.sync_enabled:
		return

	secret = settings.get_password("signature_secret", raise_exception=False) or ""
	signature = build_signature(payload, secret)
	frappe.make_post_request(
		url=settings.fastapi_webhook_url,
		data=payload,
		headers={"X-AnTek-Signature": signature, "X-AnTek-Event-Id": event_id},
		timeout=settings.request_timeout_seconds or 5,
	)
