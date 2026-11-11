# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

import json
import os

import frappe
from frappe.desk.desk_views import DeskViews
from frappe.tests import IntegrationTestCase

SALES_USER = "forms-row-user@example.com"
SALES_MANAGER = "forms-row-manager@example.com"
SYSTEM_MANAGER = "forms-row-system@example.com"


class TestFormsSetupRow(IntegrationTestCase):
	def setup_items(self):
		path = os.path.join(frappe.get_app_path("crm"), "sidebar", "module_def_fcrm", "module_def_fcrm.json")
		with open(path) as f:
			return json.load(f)["navigation_items"]

	def test_forms_is_the_first_row_of_lead_syncing_and_opens_the_forms_page(self):
		items = self.setup_items()
		section = next(i for i, item in enumerate(items) if item["key"] == "lead-syncing")

		row = items[section + 1]

		self.assertEqual(
			(row["key"], row["item_type"], row["link_to"], row["parent_key"]),
			("forms", "Page", "forms", "lead-syncing"),
		)

	def test_the_forms_page_is_a_file_of_the_fcrm_module(self):
		page = os.path.join(frappe.get_app_path("crm"), "fcrm", "frontend", "pages", "forms.js")

		self.assertTrue(os.path.exists(page))
		self.assertTrue(frappe.db.exists("Page", {"name": "forms", "module": "FCRM"}))

	def test_the_forms_page_is_permitted_to_sales_and_system_managers_only(self):
		for email, role in (
			(SALES_USER, "Sales User"),
			(SALES_MANAGER, "Sales Manager"),
			(SYSTEM_MANAGER, "System Manager"),
		):
			self.make_user(email, role)

		self.assertNotIn("forms", DeskViews.get_allowed_pages(user=SALES_USER))
		self.assertIn("forms", DeskViews.get_allowed_pages(user=SALES_MANAGER))
		self.assertIn("forms", DeskViews.get_allowed_pages(user=SYSTEM_MANAGER))

	def make_user(self, email, role):
		if not frappe.db.exists("User", email):
			user = frappe.get_doc(doctype="User", email=email, first_name=role, send_welcome_email=0).insert(
				ignore_permissions=True
			)
			user.add_roles(role)
