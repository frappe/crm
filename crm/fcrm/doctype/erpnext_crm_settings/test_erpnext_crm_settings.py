# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

import frappe
from frappe.tests import IntegrationTestCase, UnitTestCase

from crm.fcrm.doctype.erpnext_crm_settings import erpnext_crm_settings
from crm.fcrm.doctype.erpnext_crm_settings.erpnext_crm_settings import (
	get_customer_link,
	get_quotation_url,
	prefill_quotation_items,
)


class TestERPNextQuotationPermissions(IntegrationTestCase):
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


class TestERPNextCRMSettings(UnitTestCase):
	def test_quotation_url_encodes_values(self):
		settings = frappe._dict(is_erpnext_in_different_site=0, erpnext_company="Acme & Co")
		with patch.multiple(
			erpnext_crm_settings,
			_check_deal_permission=lambda crm_deal: None,
			_get_enabled_settings=lambda: settings,
			get_primary_contact=lambda crm_deal: None,
			get_organization_address=lambda organization: None,
			get_local_customer=lambda crm_deal: "Acme & Co",
			get_url_to_list=lambda doctype: "http://test/app/quotation",
		):
			url = erpnext_crm_settings.get_quotation_url("CRM-DEAL-0001")

		self.assertEqual(
			parse_qs(urlsplit(url).query),
			{
				"quotation_to": ["Customer"],
				"crm_deal": ["CRM-DEAL-0001"],
				"party_name": ["Acme & Co"],
				"company": ["Acme & Co"],
			},
		)
