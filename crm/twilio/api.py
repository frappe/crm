from werkzeug.wrappers import Response

import frappe
from twilio.rest import Client
from .twilio_handler import Twilio, IncomingCall

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

	# call_details = TwilioCallDetails(args, call_from=from_number)
	# create_call_log(call_details)
	return Response(resp.to_xml(), mimetype='text/xml')

@frappe.whitelist(allow_guest=True)
def twilio_incoming_call_handler(**kwargs):
	args = frappe._dict(kwargs)
	# call_details = TwilioCallDetails(args)
	# create_call_log(call_details)

	resp = IncomingCall(args.From, args.To).process()
	return Response(resp.to_xml(), mimetype='text/xml')

















# @frappe.whitelist(allow_guest=True)
# def twilio_incoming_call_handler(**kwargs):
# 	args = frappe._dict(kwargs)
# 	resp = VoiceResponse()

# 	resp.say("Thank you for calling! Have a great day.", voice='Polly.Amy')

# 	todo = frappe.get_doc({
# 		"doctype": "ToDo",
# 		"description": "Call from {0} to {1} is {2}".format(args.From, args.To, args.CallStatus),
# 	})
# 	todo.insert(ignore_permissions=True)


@frappe.whitelist()
def make_call(to, from_='+13134748669'):
    application_sid = 'APa7a85c103b7477c8eb25e9a8aafae055'
    account_sid = 'AC1a65d630772fbdb3a9a977c46aacef61'
    auth_token = '1eb29b621c6a60f4afdde18160bc1e2d'
    client = Client(account_sid, auth_token)

    call = client.calls.create(
        url='http://demo.twilio.com/docs/voice.xml',
        to=to,
        from_=from_
    )

    print(call.sid)