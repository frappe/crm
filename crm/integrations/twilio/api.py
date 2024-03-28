from werkzeug.wrappers import Response
import json

import frappe
from frappe import _
from .twilio_handler import Twilio, IncomingCall, TwilioCallDetails
from .utils import parse_mobile_no

@frappe.whitelist()
def is_enabled():
	return frappe.db.get_single_value("Twilio Settings", "enabled")

@frappe.whitelist()
def generate_access_token():
	"""Returns access token that is required to authenticate Twilio Client SDK.
	"""
	twilio = Twilio.connect()
	if not twilio:
		return {}

	from_number = frappe.db.get_value('Twilio Agents', frappe.session.user, 'twilio_number')
	if not from_number:
		return {
			"ok": False,
			"error": "caller_phone_identity_missing",
			"detail": "Phone number is not mapped to the caller"
		}

	token=twilio.generate_voice_access_token(identity=frappe.session.user)
	return {
		'token': frappe.safe_decode(token)
	}

@frappe.whitelist(allow_guest=True)
def voice(**kwargs):
	"""This is a webhook called by twilio to get instructions when the voice call request comes to twilio server.
	"""
	def _get_caller_number(caller):
		identity = caller.replace('client:', '').strip()
		user = Twilio.emailid_from_identity(identity)
		return frappe.db.get_value('Twilio Agents', user, 'twilio_number')

	args = frappe._dict(kwargs)
	twilio = Twilio.connect()
	if not twilio:
		return

	assert args.AccountSid == twilio.account_sid
	assert args.ApplicationSid == twilio.application_sid

	# Generate TwiML instructions to make a call
	from_number = _get_caller_number(args.Caller)
	resp = twilio.generate_twilio_dial_response(from_number, args.To)

	call_details = TwilioCallDetails(args, call_from=from_number)
	create_call_log(call_details)
	return Response(resp.to_xml(), mimetype='text/xml')

@frappe.whitelist(allow_guest=True)
def twilio_incoming_call_handler(**kwargs):
	args = frappe._dict(kwargs)
	call_details = TwilioCallDetails(args)
	create_call_log(call_details)

	resp = IncomingCall(args.From, args.To).process()
	return Response(resp.to_xml(), mimetype='text/xml')

def create_call_log(call_details: TwilioCallDetails):
	call_log = frappe.get_doc({**call_details.to_dict(),
		'doctype': 'CRM Call Log',
		'medium': 'Twilio'
	})
	call_log.reference_docname, call_log.reference_doctype = get_lead_or_deal_from_number(call_log)
	call_log.flags.ignore_permissions = True
	call_log.save()
	frappe.db.commit()

def update_call_log(call_sid, status=None):
	"""Update call log status.
	"""
	twilio = Twilio.connect()
	if not (twilio and frappe.db.exists("CRM Call Log", call_sid)): return

	call_details = twilio.get_call_info(call_sid)
	call_log = frappe.get_doc("CRM Call Log", call_sid)
	call_log.status = TwilioCallDetails.get_call_status(status or call_details.status)
	call_log.duration = call_details.duration
	call_log.start_time = get_datetime_from_timestamp(call_details.start_time)
	call_log.end_time = get_datetime_from_timestamp(call_details.end_time)
	if call_log.note and call_log.reference_docname:
		frappe.db.set_value("FCRM Note", call_log.note, "reference_doctype", call_log.reference_doctype)
		frappe.db.set_value("FCRM Note", call_log.note, "reference_docname", call_log.reference_docname)
	call_log.flags.ignore_permissions = True
	call_log.save()
	frappe.db.commit()

@frappe.whitelist(allow_guest=True)
def update_recording_info(**kwargs):
	try:
		args = frappe._dict(kwargs)
		recording_url = args.RecordingUrl
		call_sid = args.CallSid
		update_call_log(call_sid)
		frappe.db.set_value("CRM Call Log", call_sid, "recording_url", recording_url)
	except:
		frappe.log_error(title=_("Failed to capture Twilio recording"))

@frappe.whitelist(allow_guest=True)
def update_call_status_info(**kwargs):
	try:
		args = frappe._dict(kwargs)
		parent_call_sid = args.ParentCallSid
		update_call_log(parent_call_sid, status=args.CallStatus)

		call_info = {
			'ParentCallSid': args.ParentCallSid,
			'CallSid': args.CallSid,
			'CallStatus': args.CallStatus,
			'CallDuration': args.CallDuration,
			'From': args.From,
			'To': args.To,
		}

		client = Twilio.get_twilio_client()
		client.calls(args.ParentCallSid).user_defined_messages.create(
			content=json.dumps(call_info)
		)
	except:
		frappe.log_error(title=_("Failed to update Twilio call status"))

def get_datetime_from_timestamp(timestamp):
	from datetime import datetime
	from pytz import timezone

	if not timestamp: return None

	datetime_utc_tz_str = timestamp.strftime('%Y-%m-%d %H:%M:%S%z')
	datetime_utc_tz = datetime.strptime(datetime_utc_tz_str, '%Y-%m-%d %H:%M:%S%z')
	system_timezone = frappe.utils.get_system_timezone()
	converted_datetime = datetime_utc_tz.astimezone(timezone(system_timezone))
	return frappe.utils.format_datetime(converted_datetime, 'yyyy-MM-dd HH:mm:ss')

@frappe.whitelist()
def add_note_to_call_log(call_sid, note):
	"""Add note to call log. based on child call sid.
	"""
	twilio = Twilio.connect()
	if not twilio: return

	call_details = twilio.get_call_info(call_sid)
	sid = call_sid if call_details.direction == 'inbound' else call_details.parent_call_sid

	frappe.db.set_value("CRM Call Log", sid, "note", note)
	frappe.db.commit()

def get_lead_or_deal_from_number(call):
	"""Get lead/deal from the given number.
	"""

	def find_record(doctype, mobile_no, where=''):
		mobile_no = parse_mobile_no(mobile_no)
		
		query = f"""
			SELECT name, mobile_no
			FROM `tab{doctype}`
			WHERE CONCAT('+', REGEXP_REPLACE(mobile_no, '[^0-9]', '')) = {mobile_no}
		"""

		data = frappe.db.sql(query + where, as_dict=True)
		return data[0].name if data else None

	doctype = "CRM Deal"
	number = call.get('to') if call.type == 'Outgoing' else call.get('from')

	doc = find_record(doctype, number) or None
	if not doc:
		doctype = "CRM Lead"
		doc = find_record(doctype, number, 'AND converted is not True')
		if not doc:
			doc = find_record(doctype, number)

	return doc, doctype