# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from crm.api.address import get_address_display, render_without_template


class TestAddressDisplay(FrappeTestCase):
	def setUp(self):
		self.address = frappe.get_doc(
			{
				"doctype": "Address",
				"address_title": "Test Org HQ",
				"address_type": "Office",
				"address_line1": "42 Baker Street",
				"city": "London",
				"pincode": "NW1",
				"country": "United Kingdom",
				"phone": "+44 20 7946 0000",
				"email_id": "hq@example.com",
			}
		).insert(ignore_permissions=True)

	def tearDown(self):
		frappe.db.rollback()

	def test_renders_address_fields(self):
		display = get_address_display(self.address.name)

		self.assertIn("42 Baker Street", display)
		self.assertIn("London", display)
		self.assertIn("+44 20 7946 0000", display)
		self.assertIn("hq@example.com", display)

	def test_returns_none_without_a_name(self):
		self.assertIsNone(get_address_display(None))
		self.assertIsNone(get_address_display(""))

	def test_rejects_a_non_string_name(self):
		"""@frappe.whitelist() enforces the annotation on requests and in tests, so a
		dict never reaches frappe.db.exists(), where it would be read as filters."""
		for bad_name in ({"city": "London"}, ["Test Org HQ-Office"]):
			with self.assertRaises(frappe.exceptions.FrappeTypeError):
				get_address_display(bad_name)

	def test_returns_none_for_a_deleted_address(self):
		self.assertIsNone(get_address_display("Nonexistent Address-Office"))

	def test_falls_back_when_no_address_template_exists(self):
		"""A CRM site without ERPNext usually has no Address Template at all;
		frappe's render_address() throws in that case."""
		with patch(
			"crm.api.address.render_address",
			side_effect=frappe.ValidationError("No default Address Template found."),
		):
			display = get_address_display(self.address.name)

		self.assertIn("42 Baker Street", display)
		self.assertIn("London", display)
		self.assertIn("hq@example.com", display)

	def test_fallback_escapes_html(self):
		display = render_without_template({"address_line1": "<script>alert(1)</script>"})

		self.assertNotIn("<script>", display)
		self.assertIn("&lt;script&gt;", display)
