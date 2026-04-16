import socket
import frappe
import requests
from frappe import _
from frappe.integrations.utils import create_request_log

from crm.integrations.api import get_contact_by_phone_number

# Webhook URL (called from FreePBX dialplan via CURL):
# <site>/api/method/crm.integrations.freepbx.handler.handle_request?key=<webhook_secret>
#
# FreePBX dialplan CURL example (AGI or Dialplan Application):
#   exten => _X.,1,AGI(agi://127.0.0.1/crm_status.agi)
#   same  => n,System(curl -s "<webhook_url>&Status=ringing&CallerIDNum=${CALLERID(num)}&DialedNumber=${EXTEN}&UniqueID=${UNIQUEID}&Direction=incoming")


@frappe.whitelist(allow_guest=True)
def handle_request(**kwargs):
	validate_request()
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
		frappe.publish_realtime("freepbx_call", call_payload)

		status = (call_payload.get("Status") or "").lower()
		if status == "ringing":
			return

		if call_log := get_call_log(call_payload):
			update_call_log(call_payload, call_log=call_log)
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
		frappe.log_error(title="Error while creating/updating FreePBX call record")
		frappe.db.commit()
	finally:
		request_log.save(ignore_permissions=True)
		frappe.db.commit()


@frappe.whitelist()
def make_a_call(to_number: str, from_number: str | None = None, caller_id: str | None = None):
	if not is_integration_enabled():
		frappe.throw(_("Please setup FreePBX integration"), title=_("Integration Not Enabled"))

	settings = get_freepbx_settings()

	if not from_number:
		from_number = frappe.get_value(
			"CRM Telephony Agent", {"user": frappe.session.user}, "freepbx_extension"
		)

	if not from_number:
		frappe.throw(
			_("You do not have a FreePBX Extension set in your Telephony Agent"),
			title=_("Extension Missing"),
		)

	call_id = frappe.generate_hash(length=20)

	try:
		_ami_originate(
			settings=settings,
			channel=from_number,
			extension=to_number,
			context=settings.context or "from-internal",
			caller_id=caller_id or settings.caller_id or from_number,
			call_id=call_id,
		)
	except Exception as e:
		frappe.throw(str(e), title=_("FreePBX Error"))

	create_call_log(
		call_id=call_id,
		from_number=from_number,
		to_number=to_number,
		medium=caller_id or settings.caller_id or from_number,
		call_type="Outgoing",
		agent=frappe.session.user,
	)

	return {"CallSid": call_id, "From": from_number, "To": to_number}


def _ami_originate(settings, channel, extension, context, caller_id, call_id):
	"""Connect to Asterisk AMI and originate a call."""
	host = settings.host
	port = int(settings.ami_port or 5038)
	username = settings.ami_username
	password = settings.get_password("ami_password")
	webhook_url = get_status_updater_url()
	record_call = frappe.db.get_single_value("CRM FreePBX Settings", "record_call")

	with socket.create_connection((host, port), timeout=10) as s:
		s.recv(1024)  # Read AMI banner

		def send(action_str):
			s.sendall((action_str + "\r\n\r\n").encode())
			return s.recv(4096).decode(errors="ignore")

		response = send(
			f"Action: Login\r\nUsername: {username}\r\nSecret: {password}"
		)
		if "Authentication accepted" not in response:
			raise Exception(f"AMI Login failed: {response}")

		variables = (
			f"CALLUUID={call_id},"
			f"WEBHOOK_URL={webhook_url},"
			f"DESTINATION={extension},"
			f"RECORD={'yes' if record_call else 'no'}"
		)

		send(
			f"Action: Originate\r\n"
			f"ActionID: {call_id}\r\n"
			f"Channel: PJSIP/{channel}\r\n"
			f"Exten: {extension}\r\n"
			f"Context: {context}\r\n"
			f"Priority: 1\r\n"
			f"CallerID: {caller_id}\r\n"
			f"Variable: {variables}\r\n"
			f"Async: true"
		)

		send("Action: Logoff")


def get_status_updater_url():
	from frappe.utils.data import get_url

	webhook_secret = frappe.db.get_single_value("CRM FreePBX Settings", "webhook_secret")
	return get_url(f"api/method/crm.integrations.freepbx.handler.handle_request?key={webhook_secret}")


def get_freepbx_settings():
	return frappe.get_single("CRM FreePBX Settings")


def validate_request():
	webhook_secret = frappe.db.get_single_value("CRM FreePBX Settings", "webhook_secret")
	key = frappe.request.args.get("key")
	if not (key and key == webhook_secret):
		frappe.throw(_("Unauthorized request"), exc=frappe.PermissionError)


@frappe.whitelist()
def is_integration_enabled():
	return frappe.db.get_single_value("CRM FreePBX Settings", "enabled", True)


# ── Call Log helpers ────────────────────────────────────────────────────────


def create_call_log(call_id, from_number, to_number, medium, agent,
					status="Ringing", call_type="Incoming"):
	call_log = frappe.new_doc("CRM Call Log")
	call_log.id = call_id
	call_log.to = to_number
	call_log.medium = medium
	call_log.type = call_type
	call_log.status = status
	call_log.telephony_medium = "FreePBX"
	setattr(call_log, "from", from_number)

	if call_type == "Incoming":
		call_log.receiver = agent
	else:
		call_log.caller = agent

	contact_number = from_number if call_type == "Incoming" else to_number
	_link(contact_number, call_log)

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
		call_log.link_with_reference_doc(doctype, docname)


def get_call_log(call_payload):
	call_id = call_payload.get("CallSid") or call_payload.get("UniqueID")
	if call_id and frappe.db.exists("CRM Call Log", call_id):
		return frappe.get_doc("CRM Call Log", call_id)


def get_call_log_status(call_payload):
	status = (call_payload.get("DialStatus") or call_payload.get("Status") or "").lower()
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
	return mapping.get(status, "Ringing")


def update_call_log(call_payload, call_log=None):
	call_log = call_log or get_call_log(call_payload)
	if not call_log:
		return

	try:
		call_log.status = get_call_log_status(call_payload)
		call_log.to = call_payload.get("To") or call_payload.get("DialedNumber") or call_log.to
		call_log.duration = call_payload.get("Duration") or call_payload.get("BillSec") or 0
		call_log.recording_url = call_payload.get("RecordingUrl") or ""
		call_log.start_time = call_payload.get("StartTime")
		call_log.end_time = call_payload.get("EndTime")

		if call_payload.get("AgentEmail"):
			call_log.receiver = call_payload.get("AgentEmail")

		call_log.save(ignore_permissions=True)
		frappe.db.commit()
		return call_log
	except Exception:
		frappe.log_error(title="Error while updating FreePBX call record")
		frappe.db.commit()
