import frappe


def execute():
	# Sites with data are past onboarding; keep them out of the setup flow.
	if frappe.db.count("CRM Lead") or frappe.db.count("CRM Deal"):
		frappe.db.set_single_value("FCRM Settings", "setup_completed", 1)
