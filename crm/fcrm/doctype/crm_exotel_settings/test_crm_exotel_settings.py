# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

GET = "crm.fcrm.doctype.crm_exotel_settings.crm_exotel_settings.requests.get"


def response(status_code):
	return type("Response", (), {"status_code": status_code, "reason": "Unauthorized"})()


class TestCRMExotelSettings(IntegrationTestCase):
	def setUp(self):
		frappe.db.savepoint("exotel_settings_test")
		self.addCleanup(lambda: frappe.db.rollback(save_point="exotel_settings_test"))

	def save_settings(self, status_code, **values):
		settings = frappe.get_single("CRM Exotel Settings")
		settings.update(values)
		with patch(GET, return_value=response(status_code)) as get:
			settings.save()
		return get

	def test_a_save_that_turns_exotel_off_goes_through_with_revoked_credentials(self):
		self.save_settings(
			200, enabled=1, subdomain="api.exotel.com", account_sid="sid", api_key="key", api_token="token"
		)

		get = self.save_settings(401, enabled=0)

		get.assert_not_called()
		self.assertEqual(frappe.db.get_single_value("CRM Exotel Settings", "enabled"), 0)

	def test_enabling_with_bad_credentials_is_refused(self):
		with self.assertRaisesRegex(frappe.ValidationError, "valid exotel Account SID"):
			self.save_settings(
				401, enabled=1, subdomain="api.exotel.com", account_sid="sid", api_key="key", api_token="bad"
			)

		self.assertEqual(frappe.db.get_single_value("CRM Exotel Settings", "enabled"), 0)

	def test_an_unchanged_enabled_save_does_not_check_the_credentials_again(self):
		self.save_settings(
			200, enabled=1, subdomain="api.exotel.com", account_sid="sid", api_key="key", api_token="token"
		)

		get = self.save_settings(401, record_call=1)

		get.assert_not_called()

	def test_changing_a_credential_while_enabled_checks_it(self):
		self.save_settings(
			200, enabled=1, subdomain="api.exotel.com", account_sid="sid", api_key="key", api_token="token"
		)

		for field, value in (("subdomain", "api.in.exotel.com"), ("api_token", "other-token")):
			with self.subTest(field=field), self.assertRaises(frappe.ValidationError):
				self.save_settings(401, **{field: value})
