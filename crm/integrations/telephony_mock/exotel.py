import json
import uuid
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace

import frappe
from frappe import _

FIXTURES = Path(__file__).parent / "fixtures"

EVENTS = (
	"inbound_ringing",
	"inbound_completed",
	"inbound_no_answer",
	"outbound_ringing",
	"outbound_in_progress",
	"outbound_completed",
	"outbound_no_answer",
)


class FakeExotelResponse:
	"""Stands in for the `requests.Response` the handler reads."""

	def __init__(self, body):
		self.body = body

	def raise_for_status(self):
		pass

	def json(self):
		return self.body


def load_fixture(name):
	return json.loads((FIXTURES / f"{name}.json").read_text())["payload"]


def connect_call(data):
	"""The stub for `Calls/connect.json`: a Call built from what the handler posted."""
	body = load_fixture("exotel_connect_response")
	body["Call"].update(
		{
			"Sid": f"mock-out-{uuid.uuid4().hex[:12]}",
			"From": data["From"],
			"To": data["To"],
			"PhoneNumberSid": data["CallerId"],
		}
	)
	return FakeExotelResponse(body)


def get_exophones():
	"""The stub for `IncomingPhoneNumbers`: every agent's Exotel number."""
	return frappe.get_all(
		"CRM Telephony Agent", filters={"exotel_number": ["is", "set"]}, pluck="exotel_number"
	)


def post_outbound_ringing(call_sid):
	"""The first callback Exotel posts once the agent's leg is answered."""
	send_event(call_sid, "outbound_ringing")


def ring_inbound(agent=None, from_number=None):
	"""Replays an incoming call's first webhook for `agent` (default: the session user)."""
	agent = agent or frappe.session.user
	number = frappe.db.get_value("CRM Telephony Agent", agent, ["exotel_number", "mobile_no"], as_dict=True)
	if not number:
		frappe.throw(_("{0} is not a CRM Telephony Agent").format(agent))

	overrides = {
		"CallSid": f"mock-in-{uuid.uuid4().hex[:12]}",
		"AgentEmail": agent,
		"To": number.exotel_number,
		"DialWhomNumber": number.mobile_no,
	}
	if from_number:
		overrides.update({"From": from_number, "CallFrom": from_number})
	return replay(load_fixture("exotel_inbound_ringing") | overrides, agent=None)


def send_event(call_sid, event):
	"""Replays the next webhook of a call that already has a call log."""
	if event not in EVENTS:
		frappe.throw(_("Unknown Exotel event {0}").format(event))

	call_log = frappe.get_doc("CRM Call Log", call_sid)
	incoming = call_log.type == "Incoming"
	agent = call_log.receiver if incoming else call_log.caller
	customer = call_log.get("from") if incoming else call_log.to
	payload = load_fixture(f"exotel_{event}") | {"CallSid": call_sid}
	if incoming:
		payload.update({"From": customer, "CallFrom": customer, "To": call_log.medium, "AgentEmail": agent})
	else:
		payload["To"] = customer
	return replay(payload, agent=None if incoming else agent)


def replay(payload, agent):
	"""Runs the real webhook handler the way Exotel's POST would, `?agent=` included for outgoing calls."""
	from crm.integrations.exotel.handler import handle_request

	key = frappe.db.get_single_value("CRM Exotel Settings", "webhook_verify_token")
	args = {"key": key} | ({"agent": agent} if agent else {})
	with request_args(args):
		handle_request(**payload)
	return payload


@contextmanager
def request_args(args):
	"""The handler reads the query string from `frappe.request`, which a bench command or a nested call lacks."""
	previous = getattr(frappe.local, "request", None)
	frappe.local.request = SimpleNamespace(args=args, headers={})
	try:
		yield
	finally:
		frappe.local.request = previous
