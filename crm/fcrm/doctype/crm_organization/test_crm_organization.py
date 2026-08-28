# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase


class TestCRMOrganization(IntegrationTestCase):
	def tearDown(self) -> None:
		frappe.db.rollback()

	def test_negative_annual_revenue_rejected(self):
		"""Test that annual_revenue rejects negative values"""
		with self.assertRaises(frappe.NonNegativeError):
			frappe.get_doc(
				{
					"doctype": "CRM Organization",
					"organization_name": "Negative Revenue Org",
					"annual_revenue": -100,
				}
			).insert()
