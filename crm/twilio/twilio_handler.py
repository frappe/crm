import re
import json
from twilio.rest import Client as TwilioClient
from twilio.jwt.access_token import AccessToken
from twilio.jwt.access_token.grants import VoiceGrant
from twilio.twiml.voice_response import VoiceResponse, Dial
from .utils import get_public_url, merge_dicts

import frappe
from frappe import _
from frappe.utils.password import get_decrypted_password

class Twilio:
	"""Twilio connector over TwilioClient.
	"""
	def __init__(self, settings):
		"""
		:param settings: `Twilio Settings` doctype
		"""
		self.settings = settings
		self.account_sid = settings.account_sid
		self.application_sid = settings.twiml_sid
		self.api_key = settings.api_key
		self.api_secret = settings.get_password("api_secret")
		self.twilio_client = self.get_twilio_client()

	@classmethod
	def connect(self):
		"""Make a twilio connection.
		"""
		settings = frappe.get_doc("Twilio Settings")
		# if not (settings and settings.enabled):
		# 	return
		return Twilio(settings=settings)

	def get_phone_numbers(self):
		"""Get account's twilio phone numbers.
		"""
		numbers = self.twilio_client.incoming_phone_numbers.list()
		return [n.phone_number for n in numbers]

	def generate_voice_access_token(self, identity: str, ttl=60*60):
		"""Generates a token required to make voice calls from the browser.
		"""
		# identity is used by twilio to identify the user uniqueness at browser(or any endpoints).
		identity = self.safe_identity(identity)

		# Create access token with credentials
		token = AccessToken(self.account_sid, self.api_key, self.api_secret, identity=identity, ttl=ttl)

		# Create a Voice grant and add to token
		voice_grant = VoiceGrant(
			outgoing_application_sid=self.application_sid,
			incoming_allow=True, # Allow incoming calls
		)
		token.add_grant(voice_grant)
		return token.to_jwt()

	@classmethod
	def safe_identity(cls, identity: str):
		"""Create a safe identity by replacing unsupported special charaters `@` with (at)).
		Twilio Client JS fails to make a call connection if identity has special characters like @, [, / etc)
		https://www.twilio.com/docs/voice/client/errors (#31105)
		"""
		return identity.replace('@', '(at)')

	@classmethod
	def emailid_from_identity(cls, identity: str):
		"""Convert safe identity string into emailID.
		"""
		return identity.replace('(at)', '@')

	def get_recording_status_callback_url(self):
		url_path = "/api/method/twilio_integration.twilio_integration.api.update_recording_info"
		return get_public_url(url_path)

	def generate_twilio_dial_response(self, from_number: str, to_number: str):
		"""Generates voice call instructions to forward the call to agents Phone.
		"""
		resp = VoiceResponse()
		dial = Dial(
			caller_id=from_number,
			record=self.settings.record_calls,
			recording_status_callback=self.get_recording_status_callback_url(),
			recording_status_callback_event='completed'
		)
		dial.number(to_number)
		resp.append(dial)
		return resp

	def get_call_info(self, call_sid):
		return self.twilio_client.calls(call_sid).fetch()

	def generate_twilio_client_response(self, client, ring_tone='at'):
		"""Generates voice call instructions to forward the call to agents computer.
		"""
		resp = VoiceResponse()
		dial = Dial(
			ring_tone=ring_tone,
			record=self.settings.record_calls,
			recording_status_callback=self.get_recording_status_callback_url(),
			recording_status_callback_event='completed'
		)
		dial.client(client)
		resp.append(dial)
		return resp

	@classmethod
	def get_twilio_client(self):
		twilio_settings = frappe.get_doc("Twilio Settings")
		
		auth_token = get_decrypted_password("Twilio Settings", "Twilio Settings", 'auth_token')
		client = TwilioClient(twilio_settings.account_sid, auth_token)

		return client

class IncomingCall:
	def __init__(self, from_number, to_number, meta=None):
		self.from_number = from_number
		self.to_number = to_number
		self.meta = meta

	def process(self):
		"""Process the incoming call
		* Figure out who is going to pick the call (call attender)
		* Check call attender settings and forward the call to Phone
		"""
		twilio = Twilio.connect()
		owners = get_twilio_number_owners(self.to_number)
		attender = get_the_call_attender(owners)

		if not attender:
			resp = VoiceResponse()
			resp.say(_('Agent is unavailable to take the call, please call after some time.'))
			return resp

		if attender['call_receiving_device'] == 'Phone':
			return twilio.generate_twilio_dial_response(self.from_number, attender['mobile_no'])
		else:
			return twilio.generate_twilio_client_response(twilio.safe_identity(attender['name']))

def get_twilio_number_owners(phone_number):
	"""Get list of users who is using the phone_number.
	>>> get_twilio_number_owners('+11234567890')
	{
		'owner1': {'name': '..', 'mobile_no': '..', 'call_receiving_device': '...'},
		'owner2': {....}
	}
	"""
	user_voice_settings = frappe.get_all(
		'Twilio Agents',
		filters={'twilio_number': phone_number},
		fields=["name", "call_receiving_device"]
	)
	user_wise_voice_settings = {user['name']: user for user in user_voice_settings}

	user_general_settings = frappe.get_all(
		'User',
		filters = [['name', 'IN', user_wise_voice_settings.keys()]],
		fields = ['name', 'mobile_no']
	)
	user_wise_general_settings = {user['name']: user for user in user_general_settings}

	return merge_dicts(user_wise_general_settings, user_wise_voice_settings)

def get_active_loggedin_users(users):
	"""Filter the current loggedin users from the given users list
	"""
	rows = frappe.db.sql("""
		SELECT `user`
		FROM `tabSessions`
		WHERE `user` IN %(users)s
		""", {'users': users})
	return [row[0] for row in set(rows)]

def get_the_call_attender(owners):
	"""Get attender details from list of owners
	"""
	if not owners: return
	current_loggedin_users = get_active_loggedin_users(list(owners.keys()))
	for name, details in owners.items():
		if ((details['call_receiving_device'] == 'Phone' and details['mobile_no']) or
			(details['call_receiving_device'] == 'Computer' and name in current_loggedin_users)):
			return details
