# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import json

import frappe
from frappe.tests import IntegrationTestCase

from crm.fcrm.doctype.crm_fields_layout.crm_fields_layout import (
	get_fields_layout,
	get_sidepanel_sections,
	remove_deleted_field_from_layouts,
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

	def _get_stored_fieldnames(self, doctype, type):
		layout = json.loads(frappe.db.get_value("CRM Fields Layout", {"dt": doctype, "type": type}, "layout"))
		return layout[0]["columns"][0]["fields"]

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

	def test_deleting_custom_field_removes_it_from_saved_layout(self):
		self._save_layout(
			"CRM Lead",
			"Side Panel",
			[
				{
					"name": "details_section",
					"columns": [{"name": "column_1", "fields": ["first_name", "custom_layout_test_field"]}],
				}
			],
		)

		# call the Custom Field on_trash hook directly; inserting a real Custom Field
		# runs DDL, which commits implicitly and would escape the tearDown rollback
		remove_deleted_field_from_layouts(frappe._dict(dt="CRM Lead", fieldname="custom_layout_test_field"))

		self.assertEqual(self._get_stored_fieldnames("CRM Lead", "Side Panel"), ["first_name"])

	def test_patch_removes_stale_fieldnames_from_saved_layouts(self):
		from crm.patches.v1_0.remove_stale_fields_from_layouts import execute

		self._save_layout(
			"CRM Lead",
			"Side Panel",
			[
				{
					"name": "details_section",
					"columns": [
						{"name": "column_1", "fields": ["first_name", "custom_deleted_field", "email"]}
					],
				}
			],
		)

		execute()

		self.assertEqual(self._get_stored_fieldnames("CRM Lead", "Side Panel"), ["first_name", "email"])

	def test_cleanup_skips_non_string_field_entries(self):
		"""CRM always saves fieldnames as strings, but a layout written directly via the
		API may hold field dicts; cleanup must leave them alone instead of raising TypeError."""
		from crm.patches.v1_0.remove_stale_fields_from_layouts import execute

		field_dict = {"fieldname": "email", "label": "Email"}
		self._save_layout(
			"CRM Lead",
			"Side Panel",
			[
				{
					"name": "details_section",
					"columns": [
						{
							"name": "column_1",
							"fields": ["first_name", field_dict, "custom_deleted_field"],
						}
					],
				}
			],
		)

		remove_deleted_field_from_layouts(frappe._dict(dt="CRM Lead", fieldname="custom_deleted_field"))
		self.assertEqual(self._get_stored_fieldnames("CRM Lead", "Side Panel"), ["first_name", field_dict])

		execute()
		self.assertEqual(self._get_stored_fieldnames("CRM Lead", "Side Panel"), ["first_name", field_dict])
