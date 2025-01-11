import json

import bleach
import frappe
import requests
from frappe import _
from frappe.integrations.utils import create_request_log


# Incoming Call
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


# Outgoing Call
@frappe.whitelist()
def make_a_call(from_number, to_number, caller_id=None, link_to_document=None):
	if not is_integration_enabled():
		frappe.throw(_("Please setup Exotel intergration"), title=_("Integration Not Enabled"))

	endpoint = get_exotel_endpoint("Calls/connect.json?details=true")
	if not from_number:
		from_number = frappe.get_value("CRM Exotel Agent", {"user": frappe.session.user}, "mobile_no")

	if not from_number:
		frappe.throw(
			_("You do not have mobile number set in your Exotel Agent"), title=_("Mobile Number Missing")
		)

	record_call = frappe.db.get_single_value("CRM Exotel Settings", "record_call")

	try:
		response = requests.post(
			endpoint,
			data={
				"From": from_number,
				"To": to_number,
				"CallerId": caller_id,
				"Record": "true" if record_call else "false",
				"StatusCallback": get_status_updater_url(),
				"StatusCallbackEvents[0]": "terminal",
				"StatusCallbackEvents[1]": "answered"
			},
		)
		response.raise_for_status()
	except requests.exceptions.HTTPError:
		if exc := response.json().get("RestException"):
			frappe.throw(bleach.linkify(exc.get("Message")), title=_("Exotel Exception"))
	else:
		res = response.json()
		call_payload = res.get("Call", {})
		if link_to_document:
			link_to_document = json.loads(link_to_document)
		create_call_log(
			call_id=call_payload.get("Sid"),
			from_number=call_payload.get("From"),
			to_number=call_payload.get("To"),
			medium=call_payload.get("PhoneNumberSid"),
			call_type="Outgoing",
			link_to_document=link_to_document,
		)

	return response.json()


def get_exotel_endpoint(action):
	settings = get_exotel_settings()
	return "https://{api_key}:{api_token}@api.exotel.com/v1/Accounts/{sid}/{action}".format(
		api_key=settings.api_key,
		api_token=settings.get_password("api_token"),
		sid=settings.account_sid,
		action=action,
	)


def get_status_updater_url():
	from frappe.utils.data import get_url

	return get_url("api/method/crm.integrations.exotel.handler.handle_request")


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
	call_log.telephony_medium = "Exotel"
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


def get_call_log_status(call_payload, direction):
	if direction == "outbound-api" or direction == "outbound-dial":
		status = call_payload.get("Status")
		if status == "completed":
			return "Completed"
		elif status == "in-progress":
			return "In Progress"
		elif status == "busy":
			return "Ringing"
		elif status == "no-answer":
			return "No Answer"
		elif status == "failed":
			return "Failed"

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
	direction = call_payload.get("Direction")
	call_log = call_log or get_call_log(call_payload)
	status = get_call_log_status(call_payload, direction)
	try:
		if call_log:
			call_log.status = status
			# resetting this because call might be redirected to other number
			call_log.to = call_payload.get("DialWhomNumber") or call_payload.get("To")
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
