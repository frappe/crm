import socket
import time
import frappe
from frappe import _
from frappe.integrations.utils import create_request_log

from crm.integrations.api import get_contact_by_phone_number


@frappe.whitelist(allow_guest=True)
def handle_request(**kwargs):

	if not is_integration_enabled():
		return

	request_log = create_request_log(
		kwargs,
		request_description="FreePBX Call",
		service_name="FreePBX",
		request_headers=frappe.request.headers,
		is_remote_request=1,
	)

	try:

		request_log.status = "Completed"

		call_payload = kwargs

		frappe.publish_realtime(
			"freepbx_call",
			call_payload
		)

		status = (call_payload.get("Status") or "").lower()

		if status == "ringing":
			return

		if call_log := get_call_log(call_payload):

			update_call_log(
				call_payload,
				call_log=call_log
			)

		else:

			create_call_log(
				call_id=call_payload.get("CallSid") or call_payload.get("UniqueID"),
				from_number=call_payload.get("From") or call_payload.get("CallerIDNum"),
				to_number=call_payload.get("To") or call_payload.get("DialedNumber"),
				medium=call_payload.get("CallerId") or call_payload.get("Channel", ""),
				status=get_call_log_status(call_payload),
				agent=call_payload.get("AgentEmail") or frappe.session.user,
			)

	except Exception:

		request_log.status = "Failed"
		request_log.error = frappe.get_traceback()

		frappe.db.rollback()

		frappe.log_error(
			frappe.get_traceback(),
			"Error while creating/updating FreePBX call record"
		)

		frappe.db.commit()

	finally:

		request_log.save(ignore_permissions=True)
		frappe.db.commit()


@frappe.whitelist()
def get_webrtc_credentials():

	"""Return SIP/WebRTC credentials for browser registration."""

	if not is_integration_enabled():

		frappe.throw(
			_("FreePBX integration is not enabled"),
			title=_("Integration Not Enabled")
		)

	settings = get_freepbx_settings()

	agent = frappe.get_value(
		"CRM Telephony Agent",
		{"user": frappe.session.user},
		[
			"freepbx_extension",
			"freepbx_sip_username",
			"freepbx_sip_password",
		],
		as_dict=True,
	)

	if not agent or not agent.get("freepbx_sip_username"):

		frappe.throw(
			_("No FreePBX SIP credentials set in your Telephony Agent"),
			title=_("Credentials Missing"),
		)

	is_https = (
		frappe.request.environ.get("wsgi.url_scheme") == "https"
		or frappe.request.headers.get("X-Forwarded-Proto") == "https"
	)

	if is_https:
		ws_scheme = "wss"
		ws_port = settings.wss_port or 8089
	else:
		ws_scheme = "ws"
		ws_port = settings.ws_port or 8088

	agent_doc = frappe.get_doc(
		"CRM Telephony Agent",
		{"user": frappe.session.user}
	)

	return {
		"sip_uri": f"sip:{agent.freepbx_sip_username}@{settings.host}",
		"username": agent.freepbx_sip_username,
		"password": agent_doc.get_password("freepbx_sip_password"),
		"extension": agent.freepbx_extension,
		"ws_uri": f"{ws_scheme}://{settings.host}:{ws_port}/ws",
		"realm": settings.host,
		"host": settings.host,
	}


@frappe.whitelist()
def make_a_call(
	to_number: str,
	from_number: str | None = None,
	caller_id: str | None = None,
	call_type: str = "Outgoing"
):

	"""Create CRM call log only. WebRTC call handled in browser."""

	if not is_integration_enabled():

		frappe.throw(
			_("Please setup FreePBX integration"),
			title=_("Integration Not Enabled")
		)

	extension = frappe.get_value(
		"CRM Telephony Agent",
		{"user": frappe.session.user},
		"freepbx_extension"
	)

	if call_type == "Incoming":

		if not from_number:

			frappe.throw(
				_("Caller number is required for incoming call log")
			)

		log_from = from_number
		log_to = extension or to_number

	else:

		log_from = extension or from_number

		if not log_from:

			frappe.throw(
				_("You do not have a FreePBX Extension set in your Telephony Agent"),
				title=_("Extension Missing"),
			)

		log_to = to_number

	call_id = frappe.generate_hash(length=20)

	create_call_log(
		call_id=call_id,
		from_number=log_from,
		to_number=log_to,
		medium=extension or log_from,
		call_type=call_type,
		agent=frappe.session.user,
	)

	return {
		"CallSid": call_id,
		"From": log_from,
		"To": log_to,
	}


@frappe.whitelist()
def update_call_status(
	call_sid: str,
	status: str,
	duration: int = 0
):

	"""Called directly from JsSIP/WebRTC frontend."""

	from frappe.utils import now_datetime

	if not frappe.db.exists(
		"CRM Call Log",
		call_sid
	):
		return

	status_map = {
		"ringing": "Ringing",
		"in-progress": "In Progress",
		"completed": "Completed",
		"no-answer": "No Answer",
		"busy": "Busy",
		"failed": "Failed",
		"canceled": "Canceled",
	}

	db_values = {
		"status": status_map.get(
			status.lower(),
			status
		)
	}

	if duration:
		db_values["duration"] = duration

	if status.lower() == "completed":
		db_values["end_time"] = now_datetime()

	for i in range(3):

		try:

			frappe.db.set_value(
				"CRM Call Log",
				call_sid,
				db_values,
				update_modified=False
			)

			frappe.db.commit()

			return db_values["status"]

		except frappe.QueryDeadlockError:

			frappe.db.rollback()

			time.sleep(0.5)

			if i == 2:

				frappe.log_error(
					frappe.get_traceback(),
					"FreePBX Call Status Deadlock"
				)

				raise



def get_freepbx_settings():
	return frappe.get_single("CRM FreePBX Settings")



@frappe.whitelist()
def is_integration_enabled():

	return frappe.db.get_single_value(
		"CRM FreePBX Settings",
		"enabled",
		True
	)


# -------------------------------------------------------------------
# CALL LOG HELPERS
# -------------------------------------------------------------------


def create_call_log(
	call_id,
	from_number,
	to_number,
	medium,
	agent,
	status="Ringing",
	call_type="Incoming"
):

	call_log = frappe.new_doc("CRM Call Log")

	call_log.id = call_id
	call_log.to = to_number
	call_log.medium = medium
	call_log.type = call_type
	call_log.status = status
	call_log.telephony_medium = "FreePBX"

	setattr(
		call_log,
		"from",
		from_number
	)

	if call_type == "Incoming":
		call_log.receiver = agent
	else:
		call_log.caller = agent

	contact_number = (
		from_number
		if call_type == "Incoming"
		else to_number
	)

	_link(
		contact_number,
		call_log
	)

	call_log.save(ignore_permissions=True)

	frappe.db.commit()

	return call_log


def _link(contact_number, call_log):

	contact = get_contact_by_phone_number(contact_number)

	if contact.get("name"):

		doctype = "Contact"
		docname = contact.get("name")

		if contact.get("lead"):

			doctype = "CRM Lead"
			docname = contact.get("lead")

		elif contact.get("deal"):

			doctype = "CRM Deal"
			docname = contact.get("deal")

		call_log.link_with_reference_doc(
			doctype,
			docname
		)


def get_call_log(call_payload):

	call_id = (
		call_payload.get("CallSid")
		or call_payload.get("UniqueID")
	)

	if call_id and frappe.db.exists(
		"CRM Call Log",
		call_id
	):

		return frappe.get_doc(
			"CRM Call Log",
			call_id
		)


def get_call_log_status(call_payload):

	status = (
		call_payload.get("DialStatus")
		or call_payload.get("Status")
		or ""
	).lower()

	mapping = {
		"answered": "Completed",
		"completed": "Completed",
		"no-answer": "No Answer",
		"noanswer": "No Answer",
		"busy": "Busy",
		"failed": "Failed",
		"cancel": "Canceled",
		"canceled": "Canceled",
		"congestion": "Failed",
		"in-progress": "In Progress",
	}

	return mapping.get(
		status,
		"Ringing"
	)


def update_call_log(
	call_payload,
	call_log=None
):

	call_log = call_log or get_call_log(call_payload)

	if not call_log:
		return

	try:

		values = {
			"status": get_call_log_status(call_payload),
			"to": (
				call_payload.get("To")
				or call_payload.get("DialedNumber")
				or call_log.to
			),
			"duration": (
				call_payload.get("Duration")
				or call_payload.get("BillSec")
				or 0
			),
			"recording_url": (
				call_payload.get("RecordingUrl")
				or ""
			),
			"start_time": call_payload.get("StartTime"),
			"end_time": call_payload.get("EndTime"),
		}

		if call_payload.get("AgentEmail"):
			values["receiver"] = call_payload.get("AgentEmail")

		frappe.db.set_value(
			"CRM Call Log",
			call_log.name,
			values,
			update_modified=False
		)

		frappe.db.commit()

		return frappe.get_doc(
			"CRM Call Log",
			call_log.name
		)

	except Exception:

		frappe.db.rollback()

		frappe.log_error(
			frappe.get_traceback(),
			"Error while updating FreePBX call record"
		)