import frappe
from frappe import _
from frappe.model.document import Document

from crm.fcrm.doctype.crm_yeastar_settings.crm_yeastar_settings import (
	CRMYeastarSettings,
)
from crm.integrations.api import get_contact_by_phone_number

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


def create_call_log(
	call_id: str,
	from_number: str,
	to_number: str,
	medium: str,
	agent: str | None,
	status: str = "Ringing",
	call_type: str = "Incoming",
) -> "Document":
	"""Open a call log, leaving the commit to the request that opened it."""
	call_log = frappe.new_doc("CRM Call Log")
	call_log.id = call_id
	call_log.to = to_number
	call_log.medium = medium
	call_log.type = call_type
	call_log.status = status
	call_log.telephony_medium = "Yeastar"
	setattr(call_log, "from", from_number)

	if call_type == "Incoming":
		call_log.receiver = agent
	else:
		call_log.caller = agent

	link_to_contact(from_number if call_type == "Incoming" else to_number, call_log)
	call_log.save(ignore_permissions=True)

	return call_log


def link_to_contact(contact_number: str, call_log: "Document") -> None:
	contact = get_contact_by_phone_number(contact_number)
	if not contact.get("name"):
		return

	if contact.get("lead"):
		call_log.link_with_reference_doc("CRM Lead", contact["lead"])
	elif contact.get("deal"):
		call_log.link_with_reference_doc("CRM Deal", contact["deal"])
	else:
		call_log.link_with_reference_doc("Contact", contact["name"])


def handle_yeastar_error(
	error: str,
	exception: Exception | None = None,
) -> None:
	frappe.log_error(
		title=f"Yeastar {error}",
		message=frappe.get_traceback(),
	)
	frappe.throw(error, exc=exception)
