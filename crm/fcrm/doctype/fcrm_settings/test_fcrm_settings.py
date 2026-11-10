# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import json
from collections import defaultdict

import frappe
from frappe.shell.titles import app_brand
from frappe.tests import IntegrationTestCase
from frappe.tests.classes.context_managers import set_user

from crm.fcrm.doctype.fcrm_settings.fcrm_settings import brand
from crm.patches.v1_0 import encrypt_exchange_rate_access_key

FORECASTING_FIELDS = ["expected_closure_date", "probability", "expected_deal_value"]
ACCESS_KEY = "exchange-rate-test-key"


class TestFCRMSettings(IntegrationTestCase):
	def tearDown(self) -> None:
		frappe.db.rollback()

	def set_brand(self, **values):
		for field in ("brand_name", "brand_logo", "favicon"):
			frappe.db.set_single_value("FCRM Settings", field, values.get(field))
		frappe.local.request_cache = defaultdict(dict)

	def test_brand_hands_desk_the_branding_fields(self):
		self.set_brand(brand_name="Acme Sales", brand_logo="/files/acme.png", favicon="/files/acme.ico")

		self.assertEqual(
			app_brand("crm"),
			{"title": "Acme Sales", "logo": "/files/acme.png", "favicon": "/files/acme.ico"},
		)

	def test_brand_leaves_out_what_is_not_set(self):
		self.set_brand(brand_name="Acme Sales")

		self.assertEqual(app_brand("crm"), {"title": "Acme Sales"})
		self.set_brand()
		self.assertEqual(app_brand("crm"), {})

	def test_brand_is_readable_by_a_user_who_cannot_open_the_settings(self):
		self.set_brand(brand_name="Acme Sales")

		with set_user("test@example.com"):
			self.assertFalse(frappe.has_permission("FCRM Settings", "read"))
			self.assertEqual(brand()["title"], "Acme Sales")

	def test_the_brand_files_are_public_so_every_user_can_load_them(self):
		self.assertTrue(frappe.get_meta("FCRM Settings").make_attachments_public)

	def get_quick_entry_sections(self):
		layout = json.loads(frappe.db.get_value("CRM Fields Layout", "CRM Deal-Quick Entry", "layout"))
		if any("sections" in item for item in layout):
			return [section for tab in layout for section in tab.get("sections", [])]
		return layout

	def get_quick_entry_fields(self):
		return [
			field
			for section in self.get_quick_entry_sections()
			for column in section.get("columns") or []
			for field in column.get("fields") or []
		]

	def set_forecasting(self, value):
		settings = frappe.get_single("FCRM Settings")
		settings.enable_forecasting = value
		settings.save()

	def test_forecasting_adds_section_to_quick_entry(self):
		"""Enabling forecasting should append forecasting fields to the deal quick entry layout"""
		self.set_forecasting(0)
		self.assertFalse(set(FORECASTING_FIELDS) & set(self.get_quick_entry_fields()))

		self.set_forecasting(1)
		sections = self.get_quick_entry_sections()
		self.assertTrue(any(section.get("name") == "forecasted_sales_section" for section in sections))
		fields = self.get_quick_entry_fields()
		for field in FORECASTING_FIELDS:
			self.assertIn(field, fields)

	def test_disabling_forecasting_removes_section_from_quick_entry(self):
		self.set_forecasting(1)
		self.set_forecasting(0)
		sections = self.get_quick_entry_sections()
		self.assertFalse(any(section.get("name") == "forecasted_sales_section" for section in sections))

	def test_forecasting_skips_fields_already_in_quick_entry(self):
		"""Fields already placed in the layout by a manager should not be duplicated"""
		self.set_forecasting(0)

		doc = frappe.get_doc("CRM Fields Layout", "CRM Deal-Quick Entry")
		layout = json.loads(doc.layout)
		custom_section = {
			"name": "custom_section",
			"columns": [{"name": "custom_column", "fields": ["expected_deal_value"]}],
		}
		if any("sections" in item for item in layout):
			layout[-1]["sections"].append(custom_section)
		else:
			layout.append(custom_section)
		doc.layout = json.dumps(layout)
		doc.save(ignore_permissions=True)

		self.set_forecasting(1)

		fields = self.get_quick_entry_fields()
		self.assertEqual(fields.count("expected_deal_value"), 1)
		self.assertIn("expected_closure_date", fields)
		self.assertIn("probability", fields)

	def test_forecasting_adds_section_to_sidepanel(self):
		"""Side panel should get a labeled Forecasted Sales section after the contacts section"""
		self.set_forecasting(0)
		self.set_forecasting(1)

		sections = json.loads(frappe.db.get_value("CRM Fields Layout", "CRM Deal-Side Panel", "layout"))
		section = next((s for s in sections if s.get("name") == "forecasted_sales_section"), None)
		self.assertIsNotNone(section)
		self.assertEqual(section.get("label"), "Forecasted Sales")
		if sections[0].get("name") == "contacts_section":
			self.assertEqual(sections[1].get("name"), "forecasted_sales_section")
		else:
			self.assertEqual(sections[0].get("name"), "forecasted_sales_section")

		self.set_forecasting(0)
		sections = json.loads(frappe.db.get_value("CRM Fields Layout", "CRM Deal-Side Panel", "layout"))
		self.assertFalse(any(s.get("name") == "forecasted_sales_section" for s in sections))

	def test_forecasting_adds_section_to_quick_entry_with_tabs_layout(self):
		"""Layouts saved from the layout editor are wrapped in tabs and should also work"""
		self.set_forecasting(0)

		doc = frappe.get_doc("CRM Fields Layout", "CRM Deal-Quick Entry")
		layout = json.loads(doc.layout)
		if not any("sections" in item for item in layout):
			doc.layout = json.dumps([{"name": "first_tab", "sections": layout}])
			doc.save(ignore_permissions=True)

		self.set_forecasting(1)

		fields = self.get_quick_entry_fields()
		for field in FORECASTING_FIELDS:
			self.assertIn(field, fields)

	def test_the_access_key_is_kept_in_the_password_store(self):
		settings = frappe.get_single("FCRM Settings")
		settings.update({"service_provider": "exchangerate-api", "access_key": ACCESS_KEY})
		settings.save()

		self.assertEqual(frappe.get_single("FCRM Settings").access_key, "*" * len(ACCESS_KEY))
		self.assertEqual(frappe.get_single("FCRM Settings").get_password("access_key"), ACCESS_KEY)
		self.assertNotIn(ACCESS_KEY, json.dumps(frappe.get_single("FCRM Settings").as_dict(), default=str))

	def test_the_patch_moves_a_plain_access_key_into_the_password_store(self):
		frappe.db.set_single_value("FCRM Settings", "access_key", ACCESS_KEY)
		changed = [["service_provider", None, "exchangerate-api"], ["access_key", None, ACCESS_KEY]]
		frappe.get_doc(
			doctype="Version",
			ref_doctype="FCRM Settings",
			docname="FCRM Settings",
			data=json.dumps({"changed": changed}),
		).insert(ignore_permissions=True)

		encrypt_exchange_rate_access_key.execute()
		encrypt_exchange_rate_access_key.execute()

		self.assertEqual(frappe.db.get_single_value("FCRM Settings", "access_key"), "*" * len(ACCESS_KEY))
		self.assertFalse(
			frappe.get_all(
				"Version", {"ref_doctype": "FCRM Settings", "data": ["like", f"%{ACCESS_KEY}%"]}, pluck="name"
			)
		)
		self.assertEqual(frappe.get_single("FCRM Settings").get_password("access_key"), ACCESS_KEY)
