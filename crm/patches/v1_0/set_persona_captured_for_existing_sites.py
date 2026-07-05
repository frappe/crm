import frappe


def execute():
	# Existing sites already have data by upgrade time; skip onboarding for them.
	# Fresh installs are still empty here (demo data is created post setup wizard).
	if frappe.db.count("CRM Lead") or frappe.db.count("CRM Deal"):
		frappe.db.set_single_value("FCRM Settings", "persona_captured", 1)
