# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase

from crm.fcrm.doctype.crm_deal.test_crm_deal import create_test_contact, create_test_deal


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

	def test_rename_keeps_name_deals_and_contacts(self):
		deal = create_test_deal(organization="Rename Org 45895")
		contact = create_test_contact(first_name="Rename 45895", company_name="Rename Org 45895")

		frappe.rename_doc("CRM Organization", "Rename Org 45895", "Renamed Org 45895")

		org = frappe.get_doc("CRM Organization", "Renamed Org 45895")
		self.assertEqual(org.organization_name, "Renamed Org 45895")
		self.assertEqual(frappe.db.get_value("CRM Deal", deal.name, "organization"), org.name)
		self.assertEqual(frappe.db.get_value("Contact", contact.name, "company_name"), org.name)

	def test_merge_moves_contacts_to_the_kept_organization(self):
		create_test_deal(organization="Kept Org 45895")
		contact = create_test_contact(first_name="Merge 45895", company_name="Merged Org 45895")
		frappe.get_doc({"doctype": "CRM Organization", "organization_name": "Merged Org 45895"}).insert()

		frappe.rename_doc("CRM Organization", "Merged Org 45895", "Kept Org 45895", merge=True)

		self.assertFalse(frappe.db.exists("CRM Organization", "Merged Org 45895"))
		self.assertEqual(frappe.db.get_value("Contact", contact.name, "company_name"), "Kept Org 45895")

	def test_rename_leaves_other_contacts_alone(self):
		create_test_deal(organization="Alone Org 45895")
		other = create_test_contact(first_name="Other 45895", company_name="Other Org 45895")

		frappe.rename_doc("CRM Organization", "Alone Org 45895", "Alone Org 45895 B")

		self.assertEqual(frappe.db.get_value("Contact", other.name, "company_name"), "Other Org 45895")
