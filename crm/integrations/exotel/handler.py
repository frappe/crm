import frappe
from frappe import _
from frappe.integrations.utils import create_request_log


@frappe.whitelist(allow_guest=True)
def handle_request(**kwargs):
	if not is_integration_enabled():
		return

	request_log = create_request_log(
		kwargs,
		request_description="Exotel Call",
		service_name="Exotel",
		request_headers=frappe.request.headers,
		is_remote_request=1,
	)
	try:
		request_log.status = "Completed"
		exotel_settings = get_exotel_settings()
		if not exotel_settings.enabled:
			return

		call_payload = kwargs
		status = call_payload.get("Status")
		if status == "free":
			return

		if call_log := get_call_log(call_payload):
			update_call_log(call_payload, call_log=call_log)
		else:
			create_call_log(
				call_id=call_payload.get("CallSid"),
				from_number=call_payload.get("CallFrom"),
				to_number=call_payload.get("DialWhomNumber"),
				medium=call_payload.get("To"),
				status=get_call_log_status(call_payload),
			)
	except Exception:
		request_log.status = "Failed"
		request_log.error = frappe.get_traceback()
		frappe.db.rollback()
		frappe.log_error(title="Error while creating call record")
		frappe.db.commit()
	finally:
		request_log.save(ignore_permissions=True)
		frappe.db.commit()


def get_exotel_settings():
	return frappe.get_single("CRM Exotel Settings")


@frappe.whitelist()
def is_integration_enabled():
	return frappe.db.get_single_value("CRM Exotel Settings", "enabled", True)


# Call Log Functions
def create_call_log(
	call_id,
	from_number,
	to_number,
	medium,
	status="Ringing",
	call_type="Incoming",
	link_to_document=None,
):
	call_log = frappe.new_doc("CRM Call Log")
	call_log.id = call_id
	call_log.to = to_number
	call_log.medium = medium
	call_log.type = call_type
	call_log.status = status
	setattr(call_log, "from", from_number)
	if link_to_document:
		call_log.append("links", link_to_document)
	call_log.save(ignore_permissions=True)
	frappe.db.commit()
	return call_log


def get_call_log(call_payload):
	call_log_id = call_payload.get("CallSid")
	if frappe.db.exists("CRM Call Log", call_log_id):
		return frappe.get_doc("CRM Call Log", call_log_id)


def get_call_log_status(call_payload):
	status = call_payload.get("DialCallStatus")
	call_type = call_payload.get("CallType")
	dial_call_status = call_payload.get("DialCallStatus")

	if call_type == "incomplete" and dial_call_status == "no-answer":
		status = "No Answer"
	elif call_type == "client-hangup" and dial_call_status == "canceled":
		status = "Canceled"
	elif call_type == "incomplete" and dial_call_status == "failed":
		status = "Failed"
	elif call_type == "completed":
		status = "Completed"
	elif dial_call_status == "busy":
		status = "Ringing"

	return status


def update_call_log(call_payload, status="Ringing", call_log=None):
	call_log = call_log or get_call_log(call_payload)
	status = get_call_log_status(call_payload)
	try:
		if call_log:
			call_log.status = status
			# resetting this because call might be redirected to other number
			call_log.to = call_payload.get("DialWhomNumber")
			call_log.duration = (
				call_payload.get("DialCallDuration") or call_payload.get("ConversationDuration") or 0
			)
			call_log.recording_url = call_payload.get("RecordingUrl")
			call_log.start_time = call_payload.get("StartTime")
			call_log.end_time = call_payload.get("EndTime")
			call_log.save(ignore_permissions=True)
			frappe.db.commit()
			return call_log
	except Exception:
		frappe.log_error(title="Error while updating call record")
		frappe.db.commit()
