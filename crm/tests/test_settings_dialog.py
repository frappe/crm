# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

import json
import os
from unittest.mock import patch

import frappe
from frappe.shell.settings import _installed_doctypes as installed_doctypes
from frappe.shell.settings import resolve_panes
from frappe.shell.settings_filter import SettingsFilter
from frappe.tests import IntegrationTestCase
from frappe.tests.classes.context_managers import set_user

RECORDS = ("crm", "crm-frappe")
SALES_USER = "telephony-pane-user@example.com"
SALES_MANAGER = "telephony-pane-manager@example.com"
TWILIO_FIELDS = [
	"enabled",
	"account_sid",
	"auth_token",
	"app_name",
	"record_calls",
	"api_key",
	"api_secret",
	"twiml_sid",
]
TWILIO_TOKENS = ["api_key", "api_secret", "twiml_sid"]


class TestCRMSettingsDialog(IntegrationTestCase):
	def test_the_shipped_records_pass_validation(self):
		# App content validates only in developer mode, which CI sites do not set.
		with patch.dict(frappe.conf, {"developer_mode": 1}):
			for name in RECORDS:
				path = os.path.join(frappe.get_app_path("crm"), "settings_dialog", name, f"{name}.json")
				with open(path) as f:
					frappe.get_doc(json.load(f)).run_method("validate")

	def test_crm_ships_the_general_pane_on_fcrm_settings(self):
		general = self.pane("crm", "general")

		self.assertEqual(
			[(block["key"], block["save_mode"]) for block in general["blocks"]],
			[("deals", "button"), ("communication", "auto"), ("exchange-rates", "button")],
		)
		self.assertEqual(general["blocks"][2]["fields"], ["service_provider", "access_key"])
		self.assertTrue(all(block["binding"]["doctype"] == "FCRM Settings" for block in general["blocks"]))
		self.assertTrue(
			all(block["roles"] == ["Sales Manager", "System Manager"] for block in general["blocks"])
		)

	def test_only_a_manager_sees_the_general_pane(self):
		self.make_user(SALES_USER, "Sales User")
		self.make_user(SALES_MANAGER, "Sales Manager")

		with set_user(SALES_USER):
			self.assertIsNone(self.visible_pane("general"))
		with set_user(SALES_MANAGER):
			self.assertEqual(
				[block["key"] for block in self.visible_pane("general")["blocks"]],
				["deals", "communication", "exchange-rates"],
			)

	def test_crm_ships_the_telephony_pane_on_the_twilio_and_exotel_singles(self):
		telephony = self.pane("crm", "telephony")

		self.assertEqual(
			[
				(block["key"], block["binding"]["doctype"], block["save_mode"])
				for block in telephony["blocks"]
			],
			[("twilio", "CRM Twilio Settings", "button"), ("exotel", "CRM Exotel Settings", "button")],
		)
		self.assertEqual(telephony["blocks"][0]["fields"], TWILIO_FIELDS)

	def test_twilios_tokens_are_the_fields_it_holds_at_permlevel_1(self):
		meta = frappe.get_meta("CRM Twilio Settings")

		self.assertEqual(
			[name for name in TWILIO_FIELDS if meta.get_field(name).permlevel == 1], TWILIO_TOKENS
		)

	def test_a_sales_manager_sees_the_telephony_pane_with_twilios_tokens(self):
		self.make_user(SALES_MANAGER, "Sales Manager")

		with set_user(SALES_MANAGER):
			telephony = self.visible_pane("telephony")

		self.assertEqual([block["key"] for block in telephony["blocks"]], ["twilio", "exotel"])
		self.assertEqual(telephony["blocks"][0]["fields"], TWILIO_FIELDS)
		self.assertNotIn("read_only", telephony["blocks"][0])

	def test_a_reader_of_permlevel_0_only_gets_twilio_without_its_tokens(self):
		self.make_user(SALES_MANAGER, "Sales Manager")

		with (
			set_user(SALES_MANAGER),
			patch("frappe.shell.settings_filter.readable_permlevels", return_value={0}),
		):
			twilio = self.visible_pane("telephony")["blocks"][0]

		self.assertEqual(twilio["fields"], [name for name in TWILIO_FIELDS if name not in TWILIO_TOKENS])

	def test_a_sales_user_does_not_see_the_telephony_pane(self):
		self.make_user(SALES_USER, "Sales User")

		with set_user(SALES_USER):
			self.assertIsNone(self.visible_pane("telephony"))

	def test_crm_adds_a_telephony_block_to_desks_profile_pane(self):
		profile = self.pane("frappe", "profile")
		telephony = next(block for block in profile["blocks"] if block["key"] == "telephony")

		self.assertEqual(telephony["app"], "crm")
		self.assertEqual(telephony["component"], "telephony")
		self.assertEqual(
			telephony["bindings"],
			{"agent": {"type": "Record", "doctype": "CRM Telephony Agent", "resolver": "session_user"}},
		)
		self.assertEqual(
			telephony["fields"],
			["mobile_no", "default_medium", "call_receiving_device", "twilio_number", "exotel_number"],
		)
		self.assertEqual(
			[setting["label"] for setting in telephony["settings"]],
			["Mobile No.", "Default Medium", "Device", "Twilio Number", "Exotel Number"],
		)

	def test_crm_adds_an_email_accounts_block_after_desks_email_block(self):
		blocks = self.pane("frappe", "profile")["blocks"]
		keys = [block["key"] for block in blocks]

		self.assertEqual(keys[keys.index("email") + 1], "email-accounts")
		self.assertFalse(blocks[keys.index("email-accounts")].get("roles"))

	def test_a_sales_user_sees_the_email_accounts_block_in_profile(self):
		self.make_user(SALES_USER, "Sales User")

		with set_user(SALES_USER):
			profile = self.visible_pane("profile", app="frappe")
		block = next(block for block in profile["blocks"] if block["key"] == "email-accounts")

		self.assertEqual((block["app"], block["component"]), ("crm", "email-accounts"))
		self.assertFalse(block.get("bindings"))

	def test_crm_ships_a_users_pane_for_sales_and_system_managers(self):
		users = self.pane("crm", "users")

		self.assertEqual(
			[(block["key"], block["component"]) for block in users["blocks"]], [("users", "users")]
		)
		self.assertEqual(users["blocks"][0]["roles"], ["Sales Manager", "System Manager"])

	def test_only_a_manager_sees_the_users_pane(self):
		self.make_user(SALES_USER, "Sales User")
		self.make_user(SALES_MANAGER, "Sales Manager")

		with set_user(SALES_USER):
			self.assertIsNone(self.visible_pane("users"))
		with set_user(SALES_MANAGER):
			self.assertEqual([block["key"] for block in self.visible_pane("users")["blocks"]], ["users"])

	def test_crm_ships_the_erpnext_pane_with_a_product_sync_block(self):
		erpnext = self.pane("crm", "erpnext")

		self.assertEqual(
			[(block["key"], block["save_mode"]) for block in erpnext["blocks"]],
			[("erpnext", "button"), ("product-sync", "button")],
		)
		self.assertEqual(erpnext["blocks"][0]["binding"]["doctype"], "ERPNext CRM Settings")
		self.assertNotIn("sync_products", erpnext["blocks"][0]["fields"])
		self.assertEqual(erpnext["blocks"][1]["component"], "productSync")
		self.assertEqual(
			erpnext["blocks"][1]["bindings"],
			{"settings": {"type": "Single", "doctype": "ERPNext CRM Settings"}},
		)
		self.assertEqual(erpnext["blocks"][1]["fields"], ["sync_products"])
		self.assertTrue(
			all(block["roles"] == ["Sales Manager", "System Manager"] for block in erpnext["blocks"])
		)

	def test_only_a_manager_sees_the_erpnext_pane(self):
		self.make_user(SALES_USER, "Sales User")
		self.make_user(SALES_MANAGER, "Sales Manager")

		with set_user(SALES_USER):
			self.assertIsNone(self.visible_pane("erpnext"))
		with set_user(SALES_MANAGER):
			self.assertEqual(
				[block["key"] for block in self.visible_pane("erpnext")["blocks"]],
				["erpnext", "product-sync"],
			)

	def test_the_whatsapp_pane_shows_only_where_frappe_whatsapp_is_installed(self):
		with patch(
			"frappe.shell.settings._installed_doctypes",
			side_effect=lambda blocks: installed_doctypes(blocks) - {"WhatsApp Settings"},
		):
			self.assertNotIn(("crm", "whatsapp"), self.pane_addresses())

		with patch(
			"frappe.shell.settings._installed_doctypes",
			side_effect=lambda blocks: installed_doctypes(blocks) | {"WhatsApp Settings"},
		):
			whatsapp = self.pane("crm", "whatsapp")

		self.assertEqual([block["key"] for block in whatsapp["blocks"]], ["whatsapp"])
		self.assertEqual(whatsapp["blocks"][0]["binding"]["doctype"], "WhatsApp Settings")
		self.assertNotIn("fields", whatsapp["blocks"][0])
		self.assertEqual(whatsapp["blocks"][0]["roles"], ["Sales Manager", "System Manager"])

	def pane_addresses(self):
		return [(pane["app"], pane["key"]) for pane in resolve_panes()]

	def pane(self, app, key):
		return next(pane for pane in resolve_panes() if pane["app"] == app and pane["key"] == key)

	def visible_pane(self, key, app="crm"):
		panes = SettingsFilter().filter(resolve_panes())["panes"]
		return next((pane for pane in panes if pane["app"] == app and pane["key"] == key), None)

	def make_user(self, email, role):
		if not frappe.db.exists("User", email):
			user = frappe.get_doc(doctype="User", email=email, first_name=role, send_welcome_email=0).insert(
				ignore_permissions=True
			)
			user.add_roles(role)
