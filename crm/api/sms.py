import frappe
from frappe import _

from crm.api.whatsapp import validate_access
from crm.integrations.twilio.twilio_handler import Twilio
from crm.integrations.twilio.utils import get_public_url

SMS_FIELDS = [
	"name",
	"type",
	"to",
	"from",
	"message",
	"status",
	"creation",
	"reference_doctype",
	"reference_name",
	"error_message",
]


@frappe.whitelist()
def is_sms_enabled() -> bool:
	return bool(frappe.db.get_single_value("CRM Twilio Settings", "enabled"))


@frappe.whitelist()
def get_sms_messages(reference_doctype: str, reference_name: str) -> list[dict]:
	"""SMS thread of a lead/deal (a deal also includes its originating lead's thread)."""
	reference_doc = validate_access(reference_doctype, reference_name)

	messages = []
	if reference_doctype == "CRM Deal":
		lead = reference_doc.get("lead")
		if lead:
			validate_access("CRM Lead", lead)
			messages = frappe.get_all(
				"CRM SMS Message",
				filters={"reference_doctype": "CRM Lead", "reference_name": lead},
				fields=SMS_FIELDS,
			)

	messages += frappe.get_all(
		"CRM SMS Message",
		filters={"reference_doctype": reference_doctype, "reference_name": reference_name},
		fields=SMS_FIELDS,
	)
	messages.sort(key=lambda m: m.creation)
	return messages


@frappe.whitelist(methods=["POST"])
def send_sms(reference_doctype: str, reference_name: str, to: str, message: str) -> dict:
	"""Send an SMS from the current agent's Twilio number and log it on the record."""
	validate_access(reference_doctype, reference_name, permtype="write")
	message = (message or "").strip()
	if not message:
		frappe.throw(_("Message cannot be empty"))
	if not (to or "").strip():
		frappe.throw(_("Recipient number is missing"))

	doc = create_sms(
		type="Outgoing",
		from_number=get_agent_number(),
		to=to.strip(),
		message=message,
		reference_doctype=reference_doctype,
		reference_name=reference_name,
	)
	deliver_via_twilio(doc)
	return {"name": doc.name, "status": doc.status}


def get_agent_number(user: str | None = None) -> str:
	number = frappe.db.get_value("CRM Telephony Agent", user or frappe.session.user, "twilio_number")
	if not number:
		frappe.throw(
			_("Your account is not configured with a Twilio number. Please contact your administrator.")
		)
	return number


def create_sms(
	type: str,
	from_number: str,
	to: str,
	message: str,
	reference_doctype: str | None = None,
	reference_name: str | None = None,
	status: str | None = None,
):
	doc = frappe.get_doc(
		{
			"doctype": "CRM SMS Message",
			"type": type,
			"from": from_number,
			"to": to,
			"message": message,
			"status": status or ("Received" if type == "Incoming" else "Queued"),
			"telephony_medium": "Twilio",
			"reference_doctype": reference_doctype,
			"reference_name": reference_name,
		}
	)
	doc.insert(ignore_permissions=True)
	return doc


def deliver_via_twilio(doc):
	"""Push a queued outgoing message to Twilio; failures land on the doc, not the caller."""
	twilio = Twilio.connect()
	if not twilio:
		doc.db_set({"status": "Failed", "error_message": _("Twilio is not enabled")})
		return
	try:
		sent = twilio.twilio_client.messages.create(
			from_=doc.get("from"),
			to=doc.to,
			body=doc.message,
			status_callback=get_public_url("/api/method/crm.integrations.twilio.api.update_sms_status_info"),
		)
		doc.db_set({"message_sid": sent.sid, "status": "Sent"})
	except Exception:
		frappe.log_error(frappe.get_traceback(), "CRM SMS: Twilio send failed")
		doc.db_set({"status": "Failed", "error_message": _("Provider rejected the message")})


def send_automation_sms(to: str, message: str, reference_doctype=None, reference_name=None) -> bool:
	"""Channel adapter used by the automation engine: best-effort, never raises."""
	try:
		settings_number = frappe.get_all(
			"CRM Telephony Agent", filters={"twilio_number": ["is", "set"]}, pluck="twilio_number", limit=1
		)
		if not settings_number:
			return False
		doc = create_sms(
			type="Outgoing",
			from_number=settings_number[0],
			to=to,
			message=message,
			reference_doctype=reference_doctype,
			reference_name=reference_name,
		)
		deliver_via_twilio(doc)
		return doc.status == "Sent"
	except Exception:
		frappe.log_error(frappe.get_traceback(), "CRM SMS: automation send failed")
		return False
