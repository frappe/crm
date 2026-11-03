"""Dev helpers for the walk and CI. Run from a shell with
`bench --site desk.localhost execute crm.integrations.telephony_mock.dev.setup_walk --kwargs '{"user": "…"}'`,
or call the whitelisted ones from a walk; each needs `crm_telephony_mock` and `developer_mode`."""

import frappe
from frappe.utils.password import set_encrypted_password

from crm.integrations.telephony_mock import exotel, twilio
from crm.integrations.telephony_mock.mode import require_mock_mode

TWILIO_SETTINGS = {
	"enabled": 1,
	"account_sid": "ACmock00000000000000000000000000",
	"api_key": "SKmock00000000000000000000000000",
	"api_secret": "mock-api-secret",
	"auth_token": "mock-auth-token",
	"twiml_sid": "APmock00000000000000000000000000",
	"app_name": "CRM (mock)",
}
EXOTEL_SETTINGS = {
	"enabled": 1,
	"account_sid": "mock-exotel",
	"api_key": "mock-exotel-key",
	"api_token": "mock-exotel-token",
	"subdomain": "api.exotel.com",
	"webhook_verify_token": "mock-exotel-webhook-token",
}
SETTINGS = {"CRM Twilio Settings": TWILIO_SETTINGS, "CRM Exotel Settings": EXOTEL_SETTINGS}
PASSWORDS = ("api_secret", "auth_token", "api_token")
AGENT = {"mobile_no": "+919999900001", "twilio_number": "+15550100001", "exotel_number": "+918880000001"}


def setup_walk(user="Administrator", default_medium=None):
	"""Mock `CRM Twilio Settings`, `CRM Exotel Settings` and a `CRM Telephony Agent` row for `user`."""
	require_mock_mode()
	for doctype, values in SETTINGS.items():
		refuse_real_credentials(doctype, values)
	for doctype, values in SETTINGS.items():
		write_settings(doctype, values)

	refuse_real_agent(user)
	agent = (
		frappe.get_doc("CRM Telephony Agent", user)
		if frappe.db.exists("CRM Telephony Agent", user)
		else frappe.new_doc("CRM Telephony Agent")
	)
	agent.update({"user": user, "default_medium": default_medium or ""} | AGENT)
	agent.save(ignore_permissions=True)
	frappe.db.commit()


def teardown_walk(user="Administrator"):
	"""Removes what `setup_walk` and the helpers made: the agent row, the settings and the `mock-` call logs."""
	require_mock_mode()
	if frappe.db.get_value("CRM Telephony Agent", user, "twilio_number") == AGENT["twilio_number"]:
		# Blank the mock values, keep the row: the user may have had one before the mock.
		for fieldname in (*AGENT, "default_medium"):
			frappe.db.set_value("CRM Telephony Agent", user, fieldname, "")
	for doctype, values in SETTINGS.items():
		if frappe.db.get_single_value(doctype, "account_sid") == values["account_sid"]:
			write_settings(doctype, dict.fromkeys(values, ""), enabled=0)

	for name in frappe.get_all("CRM Call Log", filters={"id": ["like", "mock-%"]}, pluck="name"):
		frappe.delete_doc("CRM Call Log", name, ignore_permissions=True, force=True)
	frappe.db.delete(
		"Integration Request", {"integration_request_service": "Exotel", "data": ["like", "%mock-%"]}
	)
	frappe.db.commit()


def refuse_real_credentials(doctype, values):
	current = frappe.db.get_single_value(doctype, "account_sid")
	if current and current != values["account_sid"]:
		frappe.throw(f"{doctype} holds real credentials; the mock will not overwrite them")


def refuse_real_agent(user):
	current = frappe.db.get_value("CRM Telephony Agent", user, list(AGENT), as_dict=True)
	if current and any(value and value != AGENT[key] for key, value in current.items()):
		frappe.throw(
			f"{user} has a CRM Telephony Agent row with real numbers; the mock will not overwrite it"
		)


def write_settings(doctype, values, enabled=1):
	"""Straight to the database: saving the doctype would check the credentials against the live API."""
	for fieldname, value in values.items():
		if fieldname in PASSWORDS:
			set_encrypted_password(doctype, doctype, value, fieldname)
		else:
			frappe.db.set_single_value(doctype, fieldname, enabled if fieldname == "enabled" else value)


@frappe.whitelist()
def ring_exotel(from_number: str | None = None):
	"""An incoming Exotel call for the session user, through the real webhook handler."""
	_for_system_manager()
	return exotel.ring_inbound(from_number=from_number)


@frappe.whitelist()
def send_exotel_event(call_sid: str, event: str):
	"""The next Exotel webhook of a call: one of `exotel.EVENTS`."""
	_for_system_manager()
	return exotel.send_event(call_sid, event)


@frappe.whitelist()
def record_twilio_call(customer: str, call_type: str = "Outgoing"):
	"""The call log Twilio's webhook would make for the fake `Device`'s call; returns its `CallSid`."""
	_for_system_manager()
	return twilio.record_call(frappe.session.user, customer, call_type)


def _for_system_manager():
	require_mock_mode()
	frappe.only_for("System Manager")
