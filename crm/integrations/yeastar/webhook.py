import base64
import hashlib
import hmac
from collections.abc import Callable
from functools import wraps

import frappe
from frappe import _

from .constants import SIGNATURE_HEADER, WebhookEvent
from .utils import yeaster_settings


def verified_webhook(event: WebhookEvent) -> Callable:
	"""Reject any request not signed with the secret registered for this event."""

	def decorator(handler: Callable) -> Callable:
		@wraps(handler)
		def wrapper(*args, **kwargs):
			verify_signature(event)
			return handler(*args, **kwargs)

		return wrapper

	return decorator


def verify_signature(event: WebhookEvent) -> None:
	secret = get_webhook_secret(event)
	provided = frappe.request.headers.get(SIGNATURE_HEADER, "")
	expected = sign(frappe.request.get_data(), secret)

	if not provided or not hmac.compare_digest(expected, provided):
		reject(event, _("signature does not match the secret registered for this event"))


def sign(body: bytes, secret: str) -> str:
	digest = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).digest()
	return base64.b64encode(digest).decode("ascii")


def get_webhook_secret(event: WebhookEvent) -> str:
	secret = yeaster_settings().get_password(event.secret_field, raise_exception=False)

	if not secret:
		reject(
			event,
			_(
				"no secret is configured for this webhook. Copy it from the PBX portal "
				"into CRM Yeastar Settings before registering the event."
			),
		)

	return secret


def reject(event: WebhookEvent, reason: str) -> None:
	message = f"{event}: {reason}"
	frappe.log_error(title="Yeastar: webhook rejected", message=message)
	raise frappe.PermissionError(message)
