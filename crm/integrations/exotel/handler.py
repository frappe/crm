import frappe
import requests
from frappe import _
from frappe.integrations.utils import create_request_log

from crm.integrations.telephony.call_linking import link_call_log_to_record

# Endpoints for webhook

# Incoming Call:
# <site>/api/method/crm.integrations.exotel.handler.handle_request?key=<exotel-webhook-verify-token>

# Exotel Reference:
# https://developer.exotel.com/api/
# https://support.exotel.com/support/solutions/articles/48283-working-with-passthru-applet


# Incoming Call
@frappe.whitelist(allow_guest=True)
def handle_request(**kwargs):
	validate_request()
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

		frappe.publish_realtime("exotel_call", call_payload)
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
				agent=call_payload.get("AgentEmail"),
			)
	except Exception:
		request_log.status = "Failed"
		request_log.error = frappe.get_traceback()
		frappe.db.rollback()
		frappe.log_error(title="Error while creating/updating call record")
		frappe.db.commit()
	finally:
		request_log.save(ignore_permissions=True)
		frappe.db.commit()


# Outgoing Call
@frappe.whitelist()
def make_a_call(to_number: str, from_number: str | None = None, caller_id: str | None = None):
	if not is_integration_enabled():
		frappe.throw(_("Please setup Exotel intergration"), title=_("Integration Not Enabled"))

	endpoint = get_exotel_endpoint("Calls/connect.json?details=true")

	if not from_number:
		from_number = frappe.get_value("CRM Telephony Agent", {"user": frappe.session.user}, "mobile_no")

	if not caller_id:
		caller_id = frappe.get_value("CRM Telephony Agent", {"user": frappe.session.user}, "exotel_number")

	if not caller_id:
		frappe.throw(
			_("You do not have Exotel Number set in your Telephony Agent"), title=_("Exotel Number Missing")
		)

	if caller_id and caller_id not in get_all_exophones():
		frappe.throw(_("Exotel Number {0} is not valid").format(caller_id), title=_("Invalid Exotel Number"))

	if not from_number:
		frappe.throw(
			_("You do not have mobile number set in your Telephony Agent"), title=_("Mobile Number Missing")
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
				"StatusCallbackEvents[1]": "answered",
			},
		)
		response.raise_for_status()
	except requests.exceptions.HTTPError:
		if exc := response.json().get("RestException"):
			frappe.throw(exc.get("Message"), title=_("Exotel Exception"))
	else:
		res = response.json()
		call_payload = res.get("Call", {})

		create_call_log(
			call_id=call_payload.get("Sid"),
			from_number=call_payload.get("From"),
			to_number=call_payload.get("To"),
			medium=call_payload.get("PhoneNumberSid"),
			call_type="Outgoing",
			agent=frappe.session.user,
		)

	call_details = response.json().get("Call", {})
	call_details["CallSid"] = call_details.get("Sid", "")
	return call_details


def get_exotel_endpoint(action=None, version="v1"):
	settings = get_exotel_settings()
	return "https://{api_key}:{api_token}@{subdomain}/{version}/Accounts/{sid}/{action}".format(
		api_key=settings.api_key,
		api_token=settings.get_password("api_token"),
		subdomain=settings.subdomain,
		version=version,
		sid=settings.account_sid,
		action=action,
	)


def get_all_exophones():
	endpoint = get_exotel_endpoint("IncomingPhoneNumbers", "v2_beta")
	response = requests.get(endpoint)
	return [phone.get("friendly_name") for phone in response.json().get("incoming_phone_numbers", [])]


def get_status_updater_url():
	from frappe.utils.data import get_url

	webhook_verify_token = frappe.db.get_single_value("CRM Exotel Settings", "webhook_verify_token")
	return get_url(f"api/method/crm.integrations.exotel.handler.handle_request?key={webhook_verify_token}")


def get_exotel_settings():
	return frappe.get_single("CRM Exotel Settings")


def validate_request():
	# workaround security since exotel does not support request signature
	# /api/method/<exotel-integration-method>?key=<exotel-webhook=verify-token>
	webhook_verify_token = frappe.db.get_single_value("CRM Exotel Settings", "webhook_verify_token")
	key = frappe.request.args.get("key")
	is_valid = key and key == webhook_verify_token

	if not is_valid:
		frappe.throw(_("Unauthorized request"), exc=frappe.PermissionError)


@frappe.whitelist()
def is_integration_enabled():
	return frappe.db.get_single_value("CRM Exotel Settings", "enabled", True)


# Call Log Functions
def create_call_log(
	call_id,
	from_number,
	to_number,
	medium,
	agent,
	status="Ringing",
	call_type="Incoming",
):
	call_log = frappe.new_doc("CRM Call Log")
	call_log.id = call_id
	call_log.to = to_number
	call_log.medium = medium
	call_log.type = call_type
	call_log.status = status
	call_log.telephony_medium = "Exotel"
	setattr(call_log, "from", from_number)

	if call_type == "Incoming":
		call_log.receiver = agent
	else:
		call_log.caller = agent

	# link call log with lead/deal
	contact_number = from_number if call_type == "Incoming" else to_number
	link_call_log_to_record(call_log, contact_number)

	call_log.save(ignore_permissions=True)
	frappe.db.commit()
	return call_log


def get_call_log(call_payload):
	call_log_id = call_payload.get("CallSid")
	if frappe.db.exists("CRM Call Log", call_log_id):
		return frappe.get_doc("CRM Call Log", call_log_id)


def get_call_log_status(call_payload, direction="inbound"):
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

	call_type = call_payload.get("CallType")
	status = call_payload.get("DialCallStatus") or call_payload.get("Status")

	if call_type == "incomplete" and status == "no-answer":
		status = "No Answer"
	elif call_type == "client-hangup" and status == "canceled":
		status = "Canceled"
	elif call_type == "incomplete" and status == "failed":
		status = "Failed"
	elif call_type == "completed":
		status = "Completed"
	elif status == "busy":
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

			call_log.recording_url = (
				call_payload.get("RecordingUrl") if call_payload.get("RecordingUrl") else ""
			)

			call_log.start_time = call_payload.get("StartTime")
			call_log.end_time = call_payload.get("EndTime")

			if direction == "incoming" and call_payload.get("AgentEmail"):
				call_log.receiver = call_payload.get("AgentEmail")

			call_log.save(ignore_permissions=True)
			frappe.db.commit()
			return call_log
	except Exception:
		frappe.log_error(title="Error while updating call record")
		frappe.db.commit()


from crm.integrations.telephony.base import OutboundCallResult, TelephonyProvider
from crm.integrations.telephony.call_linking import CallEvent


class ExotelProvider(TelephonyProvider):
	provider_name = "Exotel"

	def validate_webhook(self, request_data, require_application_id=False):
		webhook_verify_token = frappe.db.get_single_value("CRM Exotel Settings", "webhook_verify_token")
		key = frappe.request.args.get("key") if frappe.request else request_data.get("key")
		if not key or key != webhook_verify_token:
			frappe.throw(_("Unauthorized request"), exc=frappe.PermissionError)
		return True

	def parse_webhook_to_event(self, request_data):
		direction_raw = request_data.get("Direction", "incoming")

		if direction_raw.startswith("outbound"):
			direction = "Outgoing"
		else:
			direction = "Incoming"

		status = get_call_log_status(request_data, direction_raw)

		# Normalize field names: Exotel uses different keys for incoming
		# webhooks (CallSid, CallFrom, DialWhomNumber) vs outbound API
		# responses (Sid, From, To, PhoneNumberSid).
		call_sid = request_data.get("CallSid") or request_data.get("Sid")
		from_number = request_data.get("CallFrom") or request_data.get("From", "")
		to_number = request_data.get("DialWhomNumber") or request_data.get("To", "")
		medium = request_data.get("To") or request_data.get("PhoneNumberSid", "")

		raw_duration = (
			request_data.get("DialCallDuration")
			or request_data.get("ConversationDuration")
		)
		duration = int(raw_duration) if raw_duration else None

		return CallEvent(
			call_sid=call_sid,
			direction=direction,
			status=status or "Ringing",
			from_number=from_number,
			to_number=to_number,
			caller="" if direction == "Incoming" else request_data.get("AgentEmail", ""),
			receiver=request_data.get("AgentEmail", "") if direction == "Incoming" else "",
			telephony_medium="Exotel",
			medium=medium,
			recording_url=request_data.get("RecordingUrl", ""),
			start_time=request_data.get("StartTime"),
			end_time=request_data.get("EndTime"),
			duration=duration,
		)

	def make_outbound_call(self, from_number, to_number, caller_user):
		result = make_a_call(to_number=to_number, from_number=from_number)
		call_sid = result.get("CallSid") or result.get("Sid") if isinstance(result, dict) else None
		return OutboundCallResult(call_sid=call_sid, provider_response=result if isinstance(result, dict) else {})

	def get_recording_credentials(self):
		return (self.settings["api_key"], self.settings["api_token"])

	def get_call_status(self, raw_status):
		return get_call_log_status({"Status": raw_status, "DialCallStatus": raw_status}, "outbound-api")

	def is_enabled(self):
		return bool(self.enabled)

	@classmethod
	def from_settings(cls):
		settings = get_exotel_settings()
		if not settings or not settings.enabled:
			return None
		return cls(
			enabled=True,
			settings={
				"account_sid": settings.account_sid,
				"api_key": settings.api_key,
				"api_token": settings.get_password("api_token"),
				"subdomain": settings.subdomain,
				"webhook_verify_token": settings.webhook_verify_token,
				"record_call": settings.record_call,
			},
		)
