from unittest import TestCase
from unittest.mock import patch

import frappe

from crm.api.command_palette import _get_recent, _search_all


class TestCommandPalette(TestCase):
	@patch("crm.api.command_palette.frappe.get_list")
	@patch("crm.api.command_palette.frappe.has_permission")
	def test_search_skips_doctypes_without_read_permission(self, has_permission, get_list):
		has_permission.side_effect = lambda doctype, _permission: doctype == "CRM Lead"
		get_list.return_value = [frappe._dict(name="LEAD-1", lead_name="Ada")]

		results = _search_all("Ada")

		self.assertEqual([result["doctype"] for result in results], ["CRM Lead"])
		self.assertEqual(get_list.call_count, 1)

	@patch("crm.api.command_palette.frappe.get_list")
	@patch("crm.api.command_palette.frappe.has_permission", return_value=True)
	def test_recents_preserve_the_users_order(self, _has_permission, get_list):
		get_list.return_value = [
			frappe._dict(name="LEAD-1", lead_name="First"),
			frappe._dict(name="LEAD-2", lead_name="Second"),
		]

		results = _get_recent({"CRM Lead": ["LEAD-2", "LEAD-1"]})

		self.assertEqual([result["name"] for result in results], ["LEAD-2", "LEAD-1"])
