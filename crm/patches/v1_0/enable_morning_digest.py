import frappe


def execute():
	# A new Check field's default only applies to new sites.
	frappe.db.set_single_value("FCRM Settings", "enable_morning_digest", 1)
