import frappe


def execute():
	if not frappe.db.get_single_value("FCRM Settings", "enable_forecasting"):
		return

	settings = frappe.get_doc("FCRM Settings")
	settings.add_forecasting_section("Quick Entry")
