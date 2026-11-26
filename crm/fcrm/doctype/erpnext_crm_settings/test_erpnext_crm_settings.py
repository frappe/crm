# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

import frappe

from crm.fcrm.doctype.erpnext_crm_settings import erpnext_crm_settings
from crm.tests import CRMTestCase as FrappeTestCase


class TestERPNextCRMSettings(FrappeTestCase):
	def test_quotation_url_encodes_values(self):
		settings = frappe._dict(is_erpnext_in_different_site=0, erpnext_company="Acme & Co")
		with patch.multiple(
			erpnext_crm_settings,
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
