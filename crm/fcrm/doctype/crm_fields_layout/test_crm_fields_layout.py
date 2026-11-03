# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import json

import frappe

from crm.fcrm.doctype.crm_fields_layout.crm_fields_layout import get_fields_layout
from crm.tests import CRMTestCase


class TestCRMFieldsLayout(CRMTestCase):
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

	def _get_stored_layout(self, doctype, type):
		return json.loads(frappe.db.get_value("CRM Fields Layout", {"dt": doctype, "type": type}, "layout"))

	def test_patch_converts_legacy_field_dicts(self):
		"""Quick Entry layouts seeded in June 2024 keep some fields as dicts keyed by `name`."""
		from crm.patches.v1_0.normalize_layout_field_entries import execute

		self._save_layout(
			"CRM Deal",
			"Quick Entry",
			[
				{
					"name": "organization_details_section",
					"columns": [
						{
							"name": "column_1",
							"fields": [
								{"label": "Organization Name", "name": "organization_name", "type": "Data"},
								"website",
							],
						},
						{"name": "column_2", "fields": []},
					],
				}
			],
		)

		execute()

		stored = self._get_stored_layout("CRM Deal", "Quick Entry")
		self.assertEqual(stored[0]["columns"][0]["fields"], ["organization_name", "website"])

		columns = get_fields_layout("CRM Deal", "Quick Entry")[0]["sections"][0]["columns"]
		self.assertEqual([f["fieldname"] for f in columns[0]["fields"]], ["organization_name", "website"])

	def test_patch_handles_tabbed_layouts_and_prefers_fieldname(self):
		from crm.patches.v1_0.normalize_layout_field_entries import execute

		self._save_layout(
			"CRM Deal",
			"Data Fields",
			[
				{
					"name": "first_tab",
					"sections": [
						{
							"name": "details_section",
							"columns": [
								{
									"name": "column_1",
									"fields": [
										{"fieldname": "website", "name": "a1b2c3"},
										{"label": "Unidentifiable"},
										"territory",
									],
								}
							],
						}
					],
				}
			],
		)

		execute()

		stored = self._get_stored_layout("CRM Deal", "Data Fields")
		self.assertEqual(stored[0]["sections"][0]["columns"][0]["fields"], ["website", "territory"])
