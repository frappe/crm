# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import json
from types import SimpleNamespace
from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from crm.patches.v1_0 import encrypt_twilio_api_secret

SECRET = "twilio-test-secret"


def fake_twilio(account_sid, auth_token):
	app = SimpleNamespace(sid="AP-test", friendly_name="Frappe CRM")
	return SimpleNamespace(
		api=SimpleNamespace(accounts=lambda sid: SimpleNamespace(fetch=lambda: None)),
		new_keys=SimpleNamespace(create=lambda friendly_name: SimpleNamespace(sid="SK-test", secret=SECRET)),
		applications=SimpleNamespace(list=lambda *args: [app], create=lambda **kwargs: app),
	)


def revoked_twilio(account_sid, auth_token):
	def reject():
		raise Exception("Twilio rejected the credentials")

	client = fake_twilio(account_sid, auth_token)
	client.api = SimpleNamespace(accounts=lambda sid: SimpleNamespace(fetch=reject))
	client.applications = SimpleNamespace(list=lambda *args: reject(), create=lambda **kwargs: reject())
	return client


CLIENT = "crm.fcrm.doctype.crm_twilio_settings.crm_twilio_settings.Client"


class TestCRMTwilioSettings(IntegrationTestCase):
	def setUp(self):
		frappe.db.savepoint("twilio_settings_test")
		self.addCleanup(lambda: frappe.db.rollback(save_point="twilio_settings_test"))

	def save_settings(self, client, **values):
		settings = frappe.get_single("CRM Twilio Settings")
		settings.update(values)
		with patch(CLIENT, side_effect=client) as twilio:
			settings.save()
		return twilio

	def test_a_save_that_turns_twilio_off_goes_through_with_revoked_credentials(self):
		self.save_settings(fake_twilio, enabled=1, account_sid="AC-test", auth_token="token")

		twilio = self.save_settings(revoked_twilio, enabled=0)

		twilio.assert_not_called()
		self.assertEqual(frappe.db.get_single_value("CRM Twilio Settings", "enabled"), 0)

	def test_enabling_with_bad_credentials_is_refused(self):
		self.save_settings(fake_twilio, enabled=0, account_sid="AC-test", auth_token="token")

		with self.assertRaisesRegex(frappe.ValidationError, "Invalid Account SID or Auth Token"):
			self.save_settings(revoked_twilio, enabled=1)

		self.assertEqual(frappe.db.get_single_value("CRM Twilio Settings", "enabled"), 0)

	def test_changing_a_credential_while_enabled_checks_it(self):
		self.save_settings(fake_twilio, enabled=1, account_sid="AC-test", auth_token="token")

		for field, value in (("account_sid", "AC-other"), ("auth_token", "other-token")):
			with self.subTest(field=field), self.assertRaises(frappe.ValidationError):
				self.save_settings(revoked_twilio, **{field: value})

	def test_a_new_account_sid_saved_while_disabled_gets_new_api_keys_on_enabling(self):
		self.save_settings(fake_twilio, enabled=1, account_sid="AC-test", auth_token="token")
		self.save_settings(fake_twilio, enabled=0, account_sid="AC-other", auth_token="token")
		self.assertFalse(frappe.db.get_single_value("CRM Twilio Settings", "api_key"))

		self.save_settings(fake_twilio, enabled=1)

		self.assertEqual(frappe.db.get_single_value("CRM Twilio Settings", "api_key"), "SK-test")

	def test_an_enabled_save_of_another_field_makes_no_twilio_call_with_revoked_credentials(self):
		self.save_settings(fake_twilio, enabled=1, account_sid="AC-test", auth_token="token")

		twilio = self.save_settings(revoked_twilio, record_calls=1)

		twilio.assert_not_called()
		self.assertEqual(frappe.db.get_single_value("CRM Twilio Settings", "record_calls"), 1)

	def test_enabling_and_changing_a_credential_while_enabled_still_call_twilio(self):
		self.save_settings(fake_twilio, enabled=0, account_sid="AC-test", auth_token="token")

		for values in ({"enabled": 1}, {"account_sid": "AC-other"}, {"auth_token": "other-token"}):
			with self.subTest(values=values):
				twilio = self.save_settings(fake_twilio, **values)

				self.assertTrue(twilio.called)

	def test_an_unchanged_enabled_save_does_not_check_the_credentials_again(self):
		self.save_settings(fake_twilio, enabled=1, account_sid="AC-test", auth_token="token")
		settings = frappe.get_single("CRM Twilio Settings")
		settings.load_doc_before_save()

		with patch.object(type(settings), "validate_twilio_account") as check:
			settings.validate()

		check.assert_not_called()

	def test_the_generated_api_secret_is_kept_in_the_password_store(self):
		settings = frappe.get_single("CRM Twilio Settings")
		settings.update({"enabled": 1, "account_sid": "AC-test", "auth_token": "token", "api_key": None})

		with patch("crm.fcrm.doctype.crm_twilio_settings.crm_twilio_settings.Client", fake_twilio):
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
