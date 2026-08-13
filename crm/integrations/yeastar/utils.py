import frappe
from frappe import _
from frappe.model.document import Document

from crm.fcrm.doctype.crm_yeastar_settings.crm_yeastar_settings import (
	CRMYeastarSettings,
)

CTA = "CRM Telephony Agent"


def yeaster_settings() -> "CRMYeastarSettings":
	return frappe.get_cached_doc("CRM Yeastar Settings")


def is_yeaster_enabled() -> None:
	error_message = "Yeastar settings are not enabled. Please configure the settings first."
	settings = yeaster_settings()

	if not settings or not settings.enabled:
		frappe.throw(_(error_message))


def get_call_log(call_log_id: str) -> "Document | None":
	if frappe.db.exists("CRM Call Log", call_log_id):
		return frappe.get_doc("CRM Call Log", call_log_id)


def get_yeaster_number() -> str:
	if not validate_session_user():
		frappe.throw(_("No Yeaster Telephony Agent found. Please configure one first."))

	caller = frappe.db.get_value(CTA, {"user": frappe.session.user, "yeastar": 1}, "yeastar_number")

	return caller


def validate_session_user() -> bool:
	return bool(frappe.db.exists(CTA, {"user": frappe.session.user, "yeastar": 1}))


def get_yeastar_agents() -> list[dict[str, str]]:
	return frappe.db.get_all(
		CTA,
		filters={"yeastar": 1},
		fields=["user", "yeastar_number"],
	)


def get_yeaster_agent_by_number(number: str) -> str:
	return frappe.db.get_value(
		CTA,
		{"yeastar": 1, "yeastar_number": number},
		"user",
	)


def handle_yeastar_error(
	error: str,
	exception: Exception | None = None,
) -> None:
	frappe.log_error(
		title=f"Yeastar {error}",
		message=frappe.get_traceback(),
	)
	frappe.throw(error, exc=exception)
