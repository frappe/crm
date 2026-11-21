# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

from unittest.mock import MagicMock, patch

import frappe
from frappe.tests import UnitTestCase

from crm.fcrm.doctype.erpnext_crm_settings import erpnext_crm_settings as module


class TestERPNextCRMSettings(UnitTestCase):
	def _create_prospect(self, known: dict[str, set[str]], territory, industry):
		"""Run create_prospect_in_remote_site against a fake remote ERPNext and return the payload it posted."""
		deal = frappe._dict(
			name="CRM-DEAL-0001",
			organization="Acme",
			lead_name="Jane",
			no_of_employees="1-10",
			deal_owner="owner@example.com",
			territory=territory,
			industry=industry,
			website=None,
			annual_revenue=0,
		)
		client = MagicMock()
		client.get_list.side_effect = lambda doctype, filters=None, **kw: (
			[{"name": filters["name"]}] if filters["name"] in known.get(doctype, set()) else []
		)
		client.post_api.return_value = "Acme"
		settings = frappe._dict(erpnext_site_url="https://erp.example.com", erpnext_company="Example GmbH")

		with (
			patch.object(module, "get_erpnext_site_client", return_value=client),
			patch.object(module.frappe, "get_cached_doc", return_value=deal),
			patch.object(module, "get_contacts", return_value=[]),
			patch.object(module, "get_organization_address", return_value=None),
		):
			self.assertEqual(module.create_prospect_in_remote_site("CRM-DEAL-0001", settings), "Acme")
		return client.post_api.call_args.args[1]

	def test_prospect_keeps_territory_and_industry_known_to_erpnext(self):
		payload = self._create_prospect(
			{"Territory": {"Germany"}, "Industry Type": {"Healthcare"}}, "Germany", "Healthcare"
		)
		self.assertEqual(payload["territory"], "Germany")
		self.assertEqual(payload["industry"], "Healthcare")

	def test_prospect_drops_territory_and_industry_unknown_to_erpnext(self):
		payload = self._create_prospect({}, "North America", "Telecom")
		self.assertEqual(payload["territory"], "")
		self.assertEqual(payload["industry"], "")

	def test_prospect_without_territory_and_industry_needs_no_lookup(self):
		payload = self._create_prospect({}, None, None)
		self.assertFalse(payload["territory"])
		self.assertFalse(payload["industry"])
