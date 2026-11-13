"""Mirror the Data Fields layouts again so each Details row lists the fields it does not place.

The mirror cleared `omitted` after frappe's `fill_form_layout_omitted` filled it, so every
unplaced field read as new and drew at its anchor.
"""

import frappe

from crm.fcrm.doctype.crm_fields_layout.form_layout_mirror import MIRRORED_DOCTYPES, mirror_layout


def execute():
	for name in frappe.get_all(
		"CRM Fields Layout",
		filters={"dt": ("in", MIRRORED_DOCTYPES), "type": "Data Fields"},
		pluck="name",
	):
		mirror_layout(frappe.get_doc("CRM Fields Layout", name))
