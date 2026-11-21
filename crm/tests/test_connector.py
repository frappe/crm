# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from crm.api.connector import return_to_connector

RETURN_TO = "https://connect.example.test/connect/return"


class TestConnector(IntegrationTestCase):
	def setUp(self):
		self.enterContext(patch.dict(frappe.conf, {"connector_hosts": ["connect.example.test"]}))

	def tearDown(self):
		frappe.local.response.pop("type", None)
		frappe.local.response.pop("location", None)

	def test_returns_to_a_listed_host_with_the_site_address(self):
		return_to_connector(RETURN_TO)

		self.assertEqual(frappe.local.response["type"], "redirect")
		location = frappe.local.response["location"]
		self.assertTrue(location.startswith(f"{RETURN_TO}?site="))

	def test_refuses_an_unlisted_host(self):
		for url in ("https://evil.example.test/connect/return", "http://connect.example.test/x"):
			with self.assertRaises(frappe.PermissionError):
				return_to_connector(url)
