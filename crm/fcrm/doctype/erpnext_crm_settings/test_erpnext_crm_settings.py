# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

import frappe
from frappe.tests import UnitTestCase

from crm.fcrm.doctype.erpnext_crm_settings import erpnext_crm_settings


class TestERPNextCRMSettings(UnitTestCase):
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

	def test_prospect_gets_the_deal_owners_email(self):
		from frappe.core.doctype.user.test_user import test_user

		settings = frappe._dict(erpnext_company="_Test Company", erpnext_site_url="https://erpnext.test")
		with test_user(roles=["Sales User"], generated_id=True) as owner:
			deal = frappe._dict(name="CRM-DEAL-TEST", deal_owner=owner.name, contacts=[], organization=None)
			with (
				patch.object(erpnext_crm_settings, "get_erpnext_site_client") as get_client,
				patch.object(frappe, "get_cached_doc", return_value=deal),
			):
				erpnext_crm_settings.create_prospect_in_remote_site(deal.name, settings)

		payload = get_client.return_value.post_api.call_args.args[1]
		self.assertEqual(payload["deal_owner"], owner.email)
