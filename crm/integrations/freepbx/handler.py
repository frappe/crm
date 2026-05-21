import time
import socket
import frappe
from frappe import _
from frappe.exceptions import QueryDeadlockError
from frappe.integrations.utils import create_request_log

from crm.integrations.api import get_contact_by_phone_number


_MAX_RETRIES = 3
_RETRY_DELAY = 0.25  # seconds, doubles each attempt


# ── Retry helper ─────────────────────────────────────────────────────────────


def _save_with_retry(call_log, apply_fn, *args, **kwargs):
	"""
	Re-fetch the document, apply field changes, and save.
	Retries up to _MAX_RETRIES times on QueryDeadlockError (MySQL 1020).

	apply_fn(call_log, *args, **kwargs) must set all fields on the doc.
	"""
	for attempt in range(1, _MAX_RETRIES + 1):
		try:
			call_log.reload()  # always work from the latest DB state
			apply_fn(call_log, *args, **kwargs)
			call_log.save(ignore_permissions=True)
			frappe.db.commit()
			return call_log
		except QueryDeadlockError:
			frappe.db.rollback()
			if attempt == _MAX_RETRIES:
				frappe.log_error(
					title="CRM Call Log deadlock – max retries exceeded",
					message=frappe.get_traceback(),
				)
				raise
			time.sleep(_RETRY_DELAY * attempt)  # 0.25s → 0.5s → 0.75s


# ── Field-setter helpers (pure, no DB calls) ─────────────────────────────────


def _apply_status_update(call_log, status, duration):
	status_map = {
		"ringing": "Ringing",
		"in-progress": "In Progress",
		"completed": "Completed",
		"no-answer": "No Answer",
		"busy": "Busy",
		"failed": "Failed",
		"canceled": "Canceled",
	}
	call_log.status = status_map.get(status.lower(), status)
	if duration:
		call_log.duration = duration
	if status.lower() == "completed":
		from frappe.utils import now_datetime
		call_log.end_time = now_datetime()


def _apply_payload_update(call_log, call_payload):
	call_log.status = get_call_log_status(call_payload)
	call_log.to = call_payload.get("To") or call_payload.get("DialedNumber") or call_log.to
	call_log.duration = call_payload.get("Duration") or call_payload.get("BillSec") or 0
	call_log.recording_url = call_payload.get("RecordingUrl") or ""
	call_log.start_time = call_payload.get("StartTime")
	call_log.end_time = call_payload.get("EndTime")
	if call_payload.get("AgentEmail"):
		call_log.receiver = call_payload.get("AgentEmail")


# ── Webhook entry point ───────────────────────────────────────────────────────


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


# ── WebRTC / browser endpoints ────────────────────────────────────────────────


@frappe.whitelist()
def get_webrtc_credentials():
	"""Return SIP/WebRTC credentials for the logged-in agent to register in the browser."""
	if not is_integration_enabled():
		frappe.throw(_("FreePBX integration is not enabled"), title=_("Integration Not Enabled"))

	settings = get_freepbx_settings()
	agent = frappe.get_value(
		"CRM Telephony Agent",
		{"user": frappe.session.user},
		["freepbx_extension", "freepbx_sip_username", "freepbx_sip_password"],
		as_dict=True,
	)

	if not agent or not agent.get("freepbx_sip_username"):
		frappe.throw(
			_("No FreePBX SIP credentials set in your Telephony Agent"),
			title=_("Credentials Missing"),
		)

	# Detect whether the request came over HTTPS or HTTP and pick the right WS scheme
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

	# Must use get_doc + get_password() to decrypt the Password fieldtype
	agent_doc = frappe.get_doc("CRM Telephony Agent", {"user": frappe.session.user})

	return {
		"sip_uri": f"sip:{agent.freepbx_sip_username}@{settings.host}",
		"username": agent.freepbx_sip_username,
		"password": agent_doc.get_password("freepbx_sip_password"),
		"extension": agent.freepbx_extension,
		"ws_uri": f"{ws_scheme}://{settings.host}/ws",
		"realm": settings.host,
		"host": settings.host,
		"ice_servers": _build_ice_servers(settings),
	}


def _build_ice_servers(settings):
	servers = []
	if settings.stun_server_url:
		servers.append({"urls": settings.stun_server_url})
	if settings.turn_server_url and settings.turn_username:
		settings_doc = frappe.get_doc("CRM FreePBX Settings")
		turn_password = settings_doc.get_password("turn_password", raise_exception=False)
		if turn_password:
			servers.append({
				"urls": settings.turn_server_url,
				"username": settings.turn_username,
				"credential": turn_password,
			})
	return servers


@frappe.whitelist()
def make_a_call(
	to_number: str,
	from_number: str | None = None,
	caller_id: str | None = None,
	call_type: str = "Outgoing",
):
	"""WebRTC mode — JsSIP handles the actual call in browser. This only creates the call log."""
	if not is_integration_enabled():
		frappe.throw(_("Please setup FreePBX integration"), title=_("Integration Not Enabled"))

	extension = frappe.get_value(
		"CRM Telephony Agent", {"user": frappe.session.user}, "freepbx_extension"
	)

	# For outgoing: from = agent extension, to = customer number
	# For incoming: from = customer number (passed), to = agent extension
	if call_type == "Incoming":
		if not from_number:
			frappe.throw(_("Caller number is required for incoming call log"))
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

	return {"CallSid": call_id, "From": log_from, "To": log_to}


@frappe.whitelist()
def update_call_status(call_sid: str, status: str, duration: int = 0):
	"""Called directly from the browser when JsSIP fires status events."""
	if not frappe.db.exists("CRM Call Log", call_sid):
		return

	call_log = frappe.get_doc("CRM Call Log", call_sid)
	result = _save_with_retry(call_log, _apply_status_update, status, duration)
	return result.status if result else None


# ── Settings ──────────────────────────────────────────────────────────────────


def get_freepbx_settings():
	return frappe.get_single("CRM FreePBX Settings")


@frappe.whitelist()
def is_integration_enabled():
	return frappe.db.get_single_value("CRM FreePBX Settings", "enabled", True)


# ── Call Log helpers ──────────────────────────────────────────────────────────


def create_call_log(
	call_id, from_number, to_number, medium, agent, status="Ringing", call_type="Incoming"
):
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
		return _save_with_retry(call_log, _apply_payload_update, call_payload)
	except Exception:
		frappe.log_error(title="Error while updating FreePBX call record")
		frappe.db.commit()
