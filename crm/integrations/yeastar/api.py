from typing import Literal

import frappe

from .constants import WebhookEvent
from .services import CallService
from .utils import yeaster_settings
from .webhook import verified_webhook


@frappe.whitelist()
def make_call(callee: str) -> dict[str, str]:
	return CallService(settings_doc=yeaster_settings()).trigger_call(callee)


@frappe.whitelist()
def respond_to_call(channel_id: str, action: Literal["accept", "refuse"]) -> dict:
	return CallService(settings_doc=yeaster_settings()).respond_to_call(channel_id, action)


@frappe.whitelist()
def hangup_call(channel_id: str) -> dict:
	return CallService(settings_doc=yeaster_settings()).hangup(channel_id)


@frappe.whitelist(allow_guest=True)  # nosemgrep
@verified_webhook(WebhookEvent.INCOMING_CALL_REQUEST)
def handle_incoming_call() -> None:
	CallService(settings_doc=yeaster_settings()).handle_incoming_call(frappe.request.get_json())


@frappe.whitelist(allow_guest=True)  # nosemgrep
@verified_webhook(WebhookEvent.CALL_STATUS_CHANGED)
def call_status_changed() -> None:
	CallService(settings_doc=yeaster_settings()).call_status_changed(frappe.request.get_json())


@frappe.whitelist(allow_guest=True)  # nosemgrep
@verified_webhook(WebhookEvent.CALL_END)
def update_call_log() -> None:
	CallService(settings_doc=yeaster_settings()).update_call_log(frappe.request.get_json())
