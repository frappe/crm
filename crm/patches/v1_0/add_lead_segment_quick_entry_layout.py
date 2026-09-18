import frappe

from crm.install import add_default_fields_layout


def execute():
	"""Create the CRM Lead Segment quick entry layout on existing sites.

	add_default_fields_layout only runs on after_install, and without this layout the
	create dialog falls back to the full meta and renders the `leads` child table grid.
	"""
	if frappe.db.exists("CRM Fields Layout", "CRM Lead Segment-Quick Entry"):
		return

	add_default_fields_layout()
