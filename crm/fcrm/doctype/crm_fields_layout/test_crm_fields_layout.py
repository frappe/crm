# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import json

import frappe
from frappe.tests import IntegrationTestCase

from crm.fcrm.doctype.crm_fields_layout.crm_fields_layout import (
	get_fields_layout,
	get_sidepanel_sections,
)


class TestCRMFieldsLayout(IntegrationTestCase):
	def tearDown(self):
		frappe.db.rollback()

	def _save_layout(self, doctype, type, layout):
		if frappe.db.exists("CRM Fields Layout", {"dt": doctype, "type": type}):
			doc = frappe.get_doc("CRM Fields Layout", {"dt": doctype, "type": type})
		else:
			doc = frappe.new_doc("CRM Fields Layout")
			doc.dt = doctype
			doc.type = type
		doc.layout = json.dumps(layout)
		doc.save()

	def test_sidepanel_drops_unresolved_fieldnames(self):
		"""A fieldname that no longer exists on the doctype (e.g. a deleted custom
		field) must not be passed through as a bare string."""
		self._save_layout(
			"CRM Lead",
			"Side Panel",
			[
				{
					"label": "Details",
					"name": "details_section",
					"columns": [{"name": "column_1", "fields": ["first_name", "custom_deleted_field"]}],
				}
			],
		)

		sections = get_sidepanel_sections("CRM Lead")
		fields = sections[0]["columns"][0]["fields"]

		self.assertEqual([f["fieldname"] for f in fields], ["first_name"])
		self.assertTrue(all(isinstance(f, dict) for f in fields))

	def test_fields_layout_drops_unresolved_fieldnames(self):
		self._save_layout(
			"CRM Lead",
			"Quick Entry",
			[
				{
					"name": "first_tab",
					"sections": [
						{
							"name": "section_1",
							"columns": [
								{
									"name": "column_1",
									"fields": ["first_name", "custom_deleted_field", "email"],
								}
							],
						}
					],
				}
			],
		)

		tabs = get_fields_layout("CRM Lead", "Quick Entry")
		fields = tabs[0]["sections"][0]["columns"][0]["fields"]

		self.assertEqual([f["fieldname"] for f in fields], ["first_name", "email"])
		self.assertTrue(all(isinstance(f, dict) for f in fields))
