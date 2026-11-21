# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase

from crm.fcrm.doctype.erpnext_crm_settings.erpnext_crm_settings import (
	get_customer_link,
	get_quotation_url,
	prefill_quotation_items,
)


class TestERPNextCRMSettings(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		deal = frappe.get_doc({"doctype": "CRM Deal", "organization": "Test Org"})
		deal.flags.ignore_mandatory = True
		deal.flags.ignore_links = True
		cls.deal = deal.insert(ignore_permissions=True).name

	def tearDown(self):
		frappe.set_user("Administrator")

	def test_quotation_helpers_need_deal_read(self):
		frappe.set_user("Guest")
		for helper in (get_customer_link, get_quotation_url, prefill_quotation_items):
			with self.subTest(helper=helper.__name__), self.assertRaises(frappe.PermissionError):
				helper(self.deal)

	def test_prefill_allowed_with_deal_read(self):
		self.assertEqual(prefill_quotation_items(self.deal), [])
