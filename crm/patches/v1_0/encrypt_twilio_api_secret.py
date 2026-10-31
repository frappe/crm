import frappe

from crm.fcrm.doctype.crm_twilio_settings.crm_twilio_settings import store_api_secret


def execute():
	secret = frappe.db.get_single_value("CRM Twilio Settings", "api_secret")
	if not secret or set(secret) == {"*"}:
		return

	frappe.db.set_single_value("CRM Twilio Settings", "api_secret", store_api_secret(secret))
