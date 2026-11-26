# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

from unittest.mock import MagicMock, patch
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
			_get_quotation_organization=lambda crm_deal, organization: None,
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


class TestERPNextQuotationAddressPermissions(UnitTestCase):
	def setUp(self):
		self.db = self.enterContext(patch.object(frappe, "db", new=MagicMock()))
		self.db.get_value.side_effect = ["Test Org", "Test Address"]
		self.address = MagicMock()
		self.address.name = "Test Address"
		self.get_address = self.enterContext(
			patch.object(frappe, "get_cached_doc", return_value=self.address)
		)
		self.permission = self.enterContext(patch.object(frappe, "has_permission"))
		self.enterContext(patch("frappe.translate.get_all_translations", return_value={}))
		self.settings = frappe._dict(is_erpnext_in_different_site=0, erpnext_company="Acme & Co")
		self._mock_quotation_helpers()

	def _mock_quotation_helpers(self):
		for name, value in {
			"_check_deal_permission": None,
			"_get_enabled_settings": self.settings,
			"get_primary_contact": None,
			"get_local_customer": None,
			"get_url_to_list": "http://test/app/quotation",
			"create_prospect_in_remote_site": "Test Prospect",
		}.items():
			self.enterContext(patch.object(erpnext_crm_settings, name, return_value=value))

	def test_rejects_another_organization_before_reading_its_address(self):
		for remote in (0, 1):
			self.settings.is_erpnext_in_different_site = remote
			self.db.get_value.side_effect = ["Test Org"]
			with self.subTest(remote=remote), self.assertRaises(frappe.PermissionError):
				get_quotation_url("CRM-DEAL-0001", "Other Org")
		self.permission.assert_not_called()
		self.get_address.assert_not_called()
		erpnext_crm_settings.create_prospect_in_remote_site.assert_not_called()

	def test_requires_organization_read_before_reading_its_address(self):
		self.permission.side_effect = frappe.PermissionError
		with self.assertRaises(frappe.PermissionError):
			get_quotation_url("CRM-DEAL-0001", "Test Org")
		self.permission.assert_called_once_with("CRM Organization", "read", doc="Test Org", throw=True)
		self.db.get_value.assert_called_once_with("CRM Deal", "CRM-DEAL-0001", "organization")
		self.get_address.assert_not_called()

	def test_requires_address_read(self):
		self.address.check_permission.side_effect = frappe.PermissionError
		with self.assertRaises(frappe.PermissionError):
			get_quotation_url("CRM-DEAL-0001", "Test Org")
		self.address.check_permission.assert_called_once_with("read")
		erpnext_crm_settings.create_prospect_in_remote_site.assert_not_called()

	def test_uses_readable_deal_address_for_local_and_remote_quotations(self):
		for remote in (0, 1):
			self.settings.is_erpnext_in_different_site = remote
			for organization in (None, "Test Org"):
				self.db.get_value.side_effect = ["Test Org", "Test Address"]
				with self.subTest(remote=remote, organization=organization):
					url = get_quotation_url("CRM-DEAL-0001", organization)
					self.assertEqual(parse_qs(urlsplit(url).query)["customer_address"], ["Test Address"])
		self.assertEqual(self.permission.call_count, 4)
		self.assertEqual(self.address.check_permission.call_count, 4)

	def test_deal_without_organization_omits_address(self):
		self.db.get_value.side_effect = [None]
		url = get_quotation_url("CRM-DEAL-0001")
		self.assertNotIn("customer_address", parse_qs(urlsplit(url).query))
		self.permission.assert_not_called()
		self.get_address.assert_not_called()

	def test_cannot_supply_organization_for_deal_without_one(self):
		self.db.get_value.side_effect = [None]
		with self.assertRaises(frappe.PermissionError):
			get_quotation_url("CRM-DEAL-0001", "Other Org")
		self.permission.assert_not_called()
		self.get_address.assert_not_called()

	def test_organization_without_address_omits_address(self):
		self.db.get_value.side_effect = ["Test Org", None]
		url = get_quotation_url("CRM-DEAL-0001", "Test Org")
		self.assertNotIn("customer_address", parse_qs(urlsplit(url).query))
		self.permission.assert_called_once_with("CRM Organization", "read", doc="Test Org", throw=True)
		self.get_address.assert_not_called()
