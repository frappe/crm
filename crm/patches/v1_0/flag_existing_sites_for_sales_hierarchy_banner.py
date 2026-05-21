import frappe


def execute():
	if frappe.flags.in_install:
		return

	frappe.db.set_single_value("FCRM Settings", "show_sales_hierarchy_banner", 1)
