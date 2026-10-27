import json

import frappe
from frappe import _
from twilio.twiml.voice_response import VoiceResponse
from werkzeug.wrappers import Response

from crm.integrations.api import get_contact_by_phone_number

from .twilio_handler import IncomingCall, Twilio, TwilioCallDetails


def validate_twilio_request(args, require_application_sid: bool = False):
	twilio = Twilio.connect()
	if not twilio:
		frappe.throw(_("Twilio configuration is missing"), frappe.PermissionError)

	account_sid = frappe.utils.cstr(args.get("AccountSid"))
	if not account_sid or account_sid != frappe.utils.cstr(twilio.account_sid):
		frappe.throw(_("Invalid Twilio account"), frappe.PermissionError)

	if require_application_sid:
		application_sid = frappe.utils.cstr(args.get("ApplicationSid"))
		if not application_sid or application_sid != frappe.utils.cstr(twilio.application_sid):
			frappe.throw(_("Invalid Twilio application"), frappe.PermissionError)

	return twilio


@frappe.whitelist()
def is_enabled():
	return frappe.db.get_single_value("CRM Twilio Settings", "enabled")


@frappe.whitelist()
def generate_access_token():
	"""Returns access token that is required to authenticate Twilio Client SDK."""
	twilio = Twilio.connect()
	if not twilio:
		return {}

	from_number = frappe.db.get_value("CRM Telephony Agent", frappe.session.user, "twilio_number")
	if not from_number:
		return {
			"ok": False,
			"error": "caller_phone_identity_missing",
			"detail": "Phone number is not mapped to the caller",
		}

	token = twilio.generate_voice_access_token(identity=frappe.session.user)
	return {"token": frappe.safe_decode(token)}


# webhook authenticity is enforced by validate_twilio_request(); guest access itself is unchanged
@frappe.whitelist(allow_guest=True)  # nosemgrep: guest-whitelisted-method
def voice(**kwargs):
	"""This is a webhook called by twilio to get instructions when the voice call request comes to twilio server."""

	def _get_caller_number(caller):
		identity = caller.replace("client:", "").strip()
		user = Twilio.emailid_from_identity(identity)
		return frappe.db.get_value("CRM Telephony Agent", user, "twilio_number")

	args = frappe._dict(kwargs)
	twilio = validate_twilio_request(args, require_application_sid=True)

	# Generate TwiML instructions to make a call
	from_number = _get_caller_number(args.Caller)
	if not from_number:
		resp = VoiceResponse()
		resp.say(_("Your account is not configured with a phone number. Please contact your administrator."))
		return Response(resp.to_xml(), mimetype="text/xml")

	call_details = TwilioCallDetails(args, call_from=from_number)
	try:
		create_call_log(call_details)
	except Exception:
		frappe.db.rollback()
		frappe.log_error(title="Error while creating Twilio call log")
		frappe.db.commit()
		return Response(_call_failed_response().to_xml(), mimetype="text/xml")

	resp = twilio.generate_twilio_dial_response(from_number, args.To)
	return Response(resp.to_xml(), mimetype="text/xml")


# webhook authenticity is enforced by validate_twilio_request(); guest access itself is unchanged
@frappe.whitelist(allow_guest=True)  # nosemgrep: guest-whitelisted-method
def twilio_incoming_call_handler(**kwargs):
	args = frappe._dict(kwargs)
	validate_twilio_request(args)

	call_details = TwilioCallDetails(args)
	try:
		create_call_log(call_details)
	except Exception:
		frappe.db.rollback()
		frappe.log_error(title="Error while creating Twilio call log")
		frappe.db.commit()
		return Response(_call_failed_response().to_xml(), mimetype="text/xml")

	resp = IncomingCall(args.From, args.To).process()
	return Response(resp.to_xml(), mimetype="text/xml")


def _call_failed_response():
	resp = VoiceResponse()
	resp.say(_("We're unable to connect your call right now. Please try again later."))
	return resp


def create_call_log(call_details: TwilioCallDetails):
	details = call_details.to_dict()

	call_log = frappe.get_doc({**details, "doctype": "CRM Call Log", "telephony_medium": "Twilio"})

	# link call log with lead/deal
	contact_number = details.get("from") if details.get("type") == "Incoming" else details.get("to")
	link(contact_number, call_log)

	call_log.save(ignore_permissions=True)
	frappe.db.commit()
	return call_log


def link(contact_number, call_log):
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


def update_call_log(call_sid, status=None):
	"""Update call log status."""
	twilio = Twilio.connect()
	if not (twilio and frappe.db.exists("CRM Call Log", call_sid)):
		return

	try:
		call_details = twilio.get_call_info(call_sid)
		call_log = frappe.get_doc("CRM Call Log", call_sid)
		call_log.status = TwilioCallDetails.get_call_status(status or call_details.status)
		call_log.duration = call_details.duration
		call_log.start_time = get_datetime_from_timestamp(call_details.start_time)
		call_log.end_time = get_datetime_from_timestamp(call_details.end_time)
		call_log.save(ignore_permissions=True)
		frappe.db.commit()
		return call_log
	except Exception:
		frappe.log_error(title="Error while updating call record")
		frappe.db.commit()


def get_twilio_settings():
	return frappe.get_single("CRM Twilio Settings")


@frappe.whitelist(allow_guest=True)
def update_recording_info(**kwargs):
	args = frappe._dict(kwargs)
	validate_twilio_request(args)

	recording_url = args.RecordingUrl
	call_sid = args.CallSid
	call_log = update_call_log(call_sid)
	if not call_log:
		frappe.throw(_("Call log not found"), frappe.DoesNotExistError)

	try:
		frappe.db.set_value("CRM Call Log", call_sid, "recording_url", recording_url)
		frappe.db.commit()
	except Exception as exc:
		frappe.log_error(title=_("Failed to capture Twilio recording"))
		raise exc


@frappe.whitelist(allow_guest=True)
def update_call_status_info(**kwargs):
	args = frappe._dict(kwargs)
	validate_twilio_request(args)

	parent_call_sid = args.ParentCallSid
	call_log = update_call_log(parent_call_sid, status=args.CallStatus)
	if not call_log:
		frappe.throw(_("Call log not found"), frappe.DoesNotExistError)

	call_info = {
		"ParentCallSid": args.ParentCallSid,
		"CallSid": args.CallSid,
		"CallStatus": args.CallStatus,
		"CallDuration": args.CallDuration,
		"From": args.From,
		"To": args.To,
	}

	try:
		client = Twilio.get_twilio_client()
		client.calls(args.ParentCallSid).user_defined_messages.create(content=json.dumps(call_info))
	except Exception as exc:
		frappe.log_error(title=_("Failed to update Twilio call status"))
		raise exc


def get_datetime_from_timestamp(timestamp):
	from datetime import datetime
	from zoneinfo import ZoneInfo

	if not timestamp:
		return None

	datetime_utc_tz_str = timestamp.strftime("%Y-%m-%d %H:%M:%S%z")
	datetime_utc_tz = datetime.strptime(datetime_utc_tz_str, "%Y-%m-%d %H:%M:%S%z")
	system_timezone = frappe.utils.get_system_timezone()
	converted_datetime = datetime_utc_tz.astimezone(ZoneInfo(system_timezone))
	return frappe.utils.format_datetime(converted_datetime, "yyyy-MM-dd HH:mm:ss")


@frappe.whitelist(allow_guest=True)
def transcription_callback(**kwargs):
	"""Webhook endpoint for Twilio real-time transcription callbacks.
	Receives streaming transcription events (both tracks) and broadcasts them to the agent
	via Frappe realtime socket while persisting final utterances in the CRM Call Log.
	"""
	args = frappe._dict(kwargs)
	if not args and frappe.request and getattr(frappe.request, "data", None):
		try:
			args = frappe._dict(json.loads(frappe.request.data))
		except Exception:
			pass

	validate_twilio_request(args)

	call_sid = args.get("CallSid")
	if not call_sid:
		return {"status": "ignored", "reason": "Missing CallSid"}

	call_log = frappe.db.get_value("CRM Call Log", call_sid, ["name", "type", "caller", "receiver"], as_dict=True)
	if not call_log and args.get("ParentCallSid"):
		call_log = frappe.db.get_value("CRM Call Log", args.get("ParentCallSid"), ["name", "type", "caller", "receiver"], as_dict=True)
	if not call_log:
		call_log = frappe.db.get_value("CRM Call Log", {"id": call_sid}, ["name", "type", "caller", "receiver"], as_dict=True)

	transcription_event = args.get("TranscriptionEvent") or args.get("event") or ""

	agent_user = None
	if call_log:
		agent_user = call_log.caller if call_log.type == "Outgoing" else call_log.receiver

	if transcription_event == "transcription-started":
		msg = {
			"call_sid": call_sid,
			"event": "started",
		}
		if agent_user:
			frappe.publish_realtime("twilio_transcription", msg, user=agent_user, after_commit=False)
		else:
			frappe.publish_realtime("twilio_transcription", msg, after_commit=False)
		return {"status": "ok"}

	elif transcription_event == "transcription-stopped":
		msg = {
			"call_sid": call_sid,
			"event": "stopped",
		}
		if agent_user:
			frappe.publish_realtime("twilio_transcription", msg, user=agent_user, after_commit=False)
		else:
			frappe.publish_realtime("twilio_transcription", msg, after_commit=False)
		return {"status": "ok"}

	# Handle transcription-content
	raw_data = args.get("TranscriptionData")
	data = {}
	if isinstance(raw_data, str):
		try:
			data = json.loads(raw_data)
		except Exception:
			data = {"transcript": raw_data}
	elif isinstance(raw_data, dict):
		data = raw_data

	transcript_text = (data.get("transcript") or "").strip()
	if not transcript_text:
		return {"status": "ok"}

	# Determine speaker: Customer or Agent
	track = args.get("Track") or ""
	speaker = None

	if track == "inbound_track":
		speaker = args.get("InboundTrackLabel") or args.get("TrackLabel")
	elif track == "outbound_track":
		speaker = args.get("OutboundTrackLabel") or args.get("TrackLabel")
	else:
		speaker = args.get("TrackLabel")

	if not speaker or speaker.lower() not in ("customer", "agent"):
		if call_log:
			if call_log.type == "Outgoing":
				speaker = "agent" if track == "inbound_track" else "customer"
			else:
				speaker = "customer" if track == "inbound_track" else "agent"
		else:
			speaker = "agent" if track == "inbound_track" else "customer"

	speaker = "customer" if speaker.lower() in ("customer", "caller", "client", "lead") else "agent"

	is_final = str(args.get("Final", "false")).lower() in ("true", "1") or bool(data.get("isFinal"))

	msg = {
		"call_sid": call_sid,
		"event": "content",
		"speaker": speaker,
		"text": transcript_text,
		"is_final": is_final,
		"sequence_id": args.get("SequenceId"),
		"timestamp": args.get("Timestamp"),
	}

	if agent_user:
		frappe.publish_realtime("twilio_transcription", msg, user=agent_user, after_commit=False)
	else:
		frappe.publish_realtime("twilio_transcription", msg, after_commit=False)

	# Atomically record final utterance to CRM Call Log
	if is_final and call_log:
		formatted_utterance = f"[{speaker.capitalize()}]\n{transcript_text}\n\n"
		frappe.db.sql(
			"""
			UPDATE `tabCRM Call Log`
			SET transcript = CONCAT(IFNULL(transcript, ''), %s)
			WHERE name = %s
			""",
			(formatted_utterance, call_log.name),
		)
		frappe.db.commit()

	return {"status": "ok"}


@frappe.whitelist()
def save_call_transcript(call_sid: str, transcript: str):
	"""Save complete formatted transcript to CRM Call Log upon call completion."""
	if not frappe.has_permission("CRM Call Log", "write", call_sid):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	call_log = frappe.get_doc("CRM Call Log", call_sid)
	if transcript and transcript.strip():
		call_log.transcript = transcript.strip()
		call_log.save(ignore_permissions=True)
		frappe.db.commit()
	return {"status": "ok", "transcript": call_log.transcript}


@frappe.whitelist()
def get_call_transcript(call_sid: str):
	"""Retrieve call transcript for a given call sid."""
	if not frappe.has_permission("CRM Call Log", "read", call_sid):
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	return frappe.db.get_value("CRM Call Log", call_sid, "transcript")
