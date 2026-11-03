import frappe
from frappe import _
from frappe.utils import cint

MOCK_TWILIO_TOKEN = "mock-twilio-token"


def is_mock_mode():
	"""Read at runtime on every call. `developer_mode` keeps production from switching it on by accident."""
	return bool(cint(frappe.conf.developer_mode) and cint(frappe.conf.crm_telephony_mock))


def require_mock_mode():
	if not is_mock_mode():
		frappe.throw(_("Telephony mock mode is off"), frappe.PermissionError)
