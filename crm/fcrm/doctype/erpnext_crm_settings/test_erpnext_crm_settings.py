# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

from unittest.mock import patch

import frappe
from frappe.tests import UnitTestCase


class TestERPNextCRMSettings(UnitTestCase):
	def test_prospect_gets_the_deal_owners_email(self):
		from frappe.core.doctype.user.test_user import test_user

		from crm.fcrm.doctype.erpnext_crm_settings import erpnext_crm_settings

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
