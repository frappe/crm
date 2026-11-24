# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import set_request

from crm.api.connector import CLIENT_ID, ensure_gateway_client, return_to_connector

GATEWAY = "https://gateway.example.test"
RETURN_TO = f"{GATEWAY}/connect/return?flow=abc"


class TestConnector(IntegrationTestCase):
	def setUp(self):
		self.enterContext(patch.dict(frappe.conf, {"mcp_gateway_url": GATEWAY}))
		set_request(method="GET", path="/", base_url="https://acme.example.test")

	def tearDown(self):
		frappe.local.response.pop("type", None)
		frappe.local.response.pop("location", None)
		frappe.db.rollback()

	def test_returns_to_the_gateway_with_the_address_the_request_came_in_on(self):
		return_to_connector(RETURN_TO)

		self.assertEqual(frappe.local.response["type"], "redirect")
		self.assertEqual(frappe.local.response["location"], f"{RETURN_TO}&site=acme.example.test")

	def test_refuses_anything_but_the_gateway(self):
		for url in ("https://evil.example.test/connect/return", "http://gateway.example.test/connect/return"):
			with self.assertRaises(frappe.PermissionError):
				return_to_connector(url)

	def test_gateway_client_is_public_and_redirects_only_to_the_gateway(self):
		frappe.delete_doc_if_exists("OAuth Client", CLIENT_ID)
		ensure_gateway_client()

		client = frappe.get_doc("OAuth Client", CLIENT_ID)
		self.assertEqual(client.redirect_uris, f"{GATEWAY}/site/callback")
		self.assertEqual(client.token_endpoint_auth_method, "None")
		self.assertFalse(client.skip_authorization)

	def test_gateway_client_follows_a_new_gateway_address(self):
		ensure_gateway_client()
		with patch.dict(frappe.conf, {"mcp_gateway_url": "https://other.example.test"}):
			ensure_gateway_client()

		redirect = frappe.db.get_value("OAuth Client", CLIENT_ID, "redirect_uris")
		self.assertEqual(redirect, "https://other.example.test/site/callback")
