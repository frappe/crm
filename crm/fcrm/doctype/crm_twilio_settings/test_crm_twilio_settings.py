# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import json
from types import SimpleNamespace
from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from crm.patches.v1_0 import encrypt_twilio_api_secret

SECRET = "twilio-test-secret"


class FakeTwilio:
	def __init__(self, account_sid, auth_token):
		app = SimpleNamespace(sid="AP-test", friendly_name="Frappe CRM")
		self.api = SimpleNamespace(accounts=lambda sid: SimpleNamespace(fetch=lambda: None))
		self.new_keys = SimpleNamespace(
			create=lambda friendly_name: SimpleNamespace(sid="SK-test", secret=SECRET)
		)
		self.applications = SimpleNamespace(list=lambda *args: [app], create=lambda **kwargs: app)


class TestCRMTwilioSettings(IntegrationTestCase):
	def setUp(self):
		frappe.db.savepoint("twilio_settings_test")
		self.addCleanup(lambda: frappe.db.rollback(save_point="twilio_settings_test"))

	def test_the_generated_api_secret_is_kept_in_the_password_store(self):
		settings = frappe.get_single("CRM Twilio Settings")
		settings.update({"enabled": 1, "account_sid": "AC-test", "auth_token": "token", "api_key": None})

		with patch("crm.fcrm.doctype.crm_twilio_settings.crm_twilio_settings.Client", FakeTwilio):
			settings.save()

		self.assertNotIn(SECRET, (settings.api_secret, self.stored_secret()))
		self.assertFalse(self.versions_holding_the_secret())
		self.assertEqual(frappe.get_single("CRM Twilio Settings").get_password("api_secret"), SECRET)

	def test_the_patch_moves_a_plain_api_secret_into_the_password_store(self):
		frappe.db.set_single_value("CRM Twilio Settings", "api_secret", SECRET)
		frappe.get_doc(
			doctype="Version",
			ref_doctype="CRM Twilio Settings",
			docname="CRM Twilio Settings",
			data=json.dumps({"changed": [["api_key", None, "SK-test"], ["api_secret", None, SECRET]]}),
		).insert(ignore_permissions=True)

		encrypt_twilio_api_secret.execute()

		self.assertEqual(self.stored_secret(), "*" * len(SECRET))
		self.assertFalse(self.versions_holding_the_secret())
		self.assertEqual(frappe.get_single("CRM Twilio Settings").get_password("api_secret"), SECRET)

	def versions_holding_the_secret(self):
		return frappe.get_all(
			"Version", {"ref_doctype": "CRM Twilio Settings", "data": ["like", f"%{SECRET}%"]}, pluck="name"
		)

	def stored_secret(self):
		return frappe.db.get_single_value("CRM Twilio Settings", "api_secret")
