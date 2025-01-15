import frappe


@frappe.whitelist()
def is_call_integration_enabled():
	twilio_enabled = frappe.db.get_single_value("Twilio Settings", "enabled")
	exotel_enabled = frappe.db.get_single_value("CRM Exotel Settings", "enabled")
	default_calling_medium = frappe.db.get_single_value("FCRM Settings", "default_calling_medium")

	return {
		"twilio_enabled": twilio_enabled,
		"exotel_enabled": exotel_enabled,
		"default_calling_medium": default_calling_medium,
	}


@frappe.whitelist()
def set_default_calling_medium(medium):
	return frappe.db.set_value("FCRM Settings", "FCRM Settings", "default_calling_medium", medium)
