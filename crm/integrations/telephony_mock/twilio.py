import uuid

import frappe
from frappe import _

from crm.integrations.telephony_mock.mode import MOCK_TWILIO_TOKEN


def access_token():
	"""`generate_access_token` in mock mode: the browser's fake `Device` ignores the token."""
	return {"token": MOCK_TWILIO_TOKEN, "mock": True}


def record_call(agent, customer, call_type="Outgoing"):
	"""Runs Twilio's real call-log code with the args its webhook would carry; the fake `Device` makes no webhook."""
	from crm.integrations.twilio.api import create_call_log
	from crm.integrations.twilio.twilio_handler import Twilio, TwilioCallDetails

	number = frappe.db.get_value("CRM Telephony Agent", agent, "twilio_number")
	if not number:
		frappe.throw(_("{0} has no Twilio number").format(agent))

	outgoing = call_type == "Outgoing"
	settings = frappe.get_single("CRM Twilio Settings")
	call_sid = f"mock-tw-{uuid.uuid4().hex[:12]}"
	args = frappe._dict(
		AccountSid=settings.account_sid,
		ApplicationSid=settings.twiml_sid,
		CallSid=call_sid,
		CallStatus="in-progress",
		Caller=f"client:{Twilio.safe_identity(agent)}" if outgoing else customer,
		From=number if outgoing else customer,
		To=customer if outgoing else number,
	)
	create_call_log(TwilioCallDetails(args))
	return call_sid
