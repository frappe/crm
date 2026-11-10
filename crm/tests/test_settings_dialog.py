# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

import json
import os
from unittest.mock import patch

import frappe
from frappe.desk.doctype.settings_dialog.settings_dialog import SettingsDialog
from frappe.desk.settings_rules import SettingsRules
from frappe.shell.settings import merge_settings, resolve_panes
from frappe.shell.settings_filter import SettingsFilter
from frappe.shell.settings_sidebar import filter_sidebar
from frappe.shell.settings_sidebar_text import assert_settings_sidebar
from frappe.tests import IntegrationTestCase
from frappe.tests.classes.context_managers import set_user

RECORDS = ("crm", "crm-frappe")
SALES_USER = "telephony-pane-user@example.com"
SALES_MANAGER = "telephony-pane-manager@example.com"
SYSTEM_MANAGER = "regional-block-manager@example.com"
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
					record = json.load(f)
				SettingsDialog.prepare_for_import(record)
				frappe.get_doc(record).run_method("validate")

	def test_the_crm_sidebar_matches_its_snapshot(self):
		assert_settings_sidebar("crm")

	def test_crm_ships_the_general_pane_on_fcrm_settings(self):
		general = self.pane("crm", "general")

		self.assertEqual(
			[(block["key"], block["save_mode"]) for block in general["blocks"]],
			[
				("brand", "button"),
				("deals", "button"),
				("communication", "auto"),
				("exchange-rates", "button"),
			],
		)
		self.assertEqual(general["blocks"][0]["fields"], ["brand_name", "brand_logo", "favicon"])
		self.assertEqual(general["blocks"][3]["fields"], ["service_provider", "access_key"])
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
				["brand", "deals", "communication", "exchange-rates"],
			)

	def test_general_places_the_regional_block_after_exchange_rates(self):
		self.assertEqual(
			self.sidebar_blocks("crm/general"),
			[
				"crm/general/brand",
				"crm/general/deals",
				"crm/general/communication",
				"crm/general/exchange-rates",
				"desk/system/regional",
			],
		)

	def test_only_a_system_manager_sees_the_regional_block_in_general(self):
		self.make_user(SALES_MANAGER, "Sales Manager")
		self.make_user(SYSTEM_MANAGER, "System Manager")

		with set_user(SALES_MANAGER):
			self.assertEqual(
				self.sidebar_blocks("crm/general"),
				[
					"crm/general/brand",
					"crm/general/deals",
					"crm/general/communication",
					"crm/general/exchange-rates",
				],
			)
		with set_user(SYSTEM_MANAGER):
			self.assertEqual(self.sidebar_blocks("crm/general")[-1], "desk/system/regional")

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

	def test_crm_adds_its_profile_blocks_after_desks_own(self):
		blocks = self.pane("frappe", "profile")["blocks"]
		keys = [block["key"] for block in blocks]

		crm_keys = [block["key"] for block in blocks if block["app"] == "crm"]
		first_crm = keys.index(crm_keys[0])

		self.assertEqual(crm_keys, ["telephony", "email-accounts"])
		self.assertTrue(all(block["app"] == "frappe" for block in blocks[:first_crm]))
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
			[(block["key"], block["component"]) for block in users["blocks"]],
			[("users", "users"), ("invite", "invite"), ("sales-hierarchy", "sales-hierarchy")],
		)
		self.assertTrue(
			all(block["roles"] == ["Sales Manager", "System Manager"] for block in users["blocks"])
		)

	def test_only_a_manager_sees_the_users_pane(self):
		self.make_user(SALES_USER, "Sales User")
		self.make_user(SALES_MANAGER, "Sales Manager")

		with set_user(SALES_USER):
			self.assertIsNone(self.visible_pane("users"))
		with set_user(SALES_MANAGER):
			self.assertEqual(
				[block["key"] for block in self.visible_pane("users")["blocks"]],
				["users", "invite", "sales-hierarchy"],
			)

	def test_crm_ships_a_forms_pane_for_sales_and_system_managers(self):
		forms = self.pane("crm", "forms")

		self.assertEqual([(block["key"], block["component"]) for block in forms["blocks"]], [("forms", "forms")])
		self.assertEqual(forms["blocks"][0]["roles"], ["Sales Manager", "System Manager"])

	def test_only_a_manager_sees_the_forms_pane(self):
		self.make_user(SALES_USER, "Sales User")
		self.make_user(SALES_MANAGER, "Sales Manager")

		with set_user(SALES_USER):
			self.assertIsNone(self.visible_pane("forms"))
		with set_user(SALES_MANAGER):
			self.assertEqual([block["key"] for block in self.visible_pane("forms")["blocks"]], ["forms"])

	def test_crm_ships_the_erpnext_pane_with_verify_connection_and_product_sync_blocks(self):
		erpnext = self.pane("crm", "erpnext")

		self.assertEqual(
			[(block["key"], block["save_mode"]) for block in erpnext["blocks"]],
			[("erpnext", "button"), ("verify-connection", "button"), ("product-sync", "button")],
		)
		self.assertEqual(erpnext["blocks"][0]["binding"]["doctype"], "ERPNext CRM Settings")
		self.assertNotIn("sync_products", erpnext["blocks"][0]["fields"])
		self.assertEqual(erpnext["blocks"][1]["component"], "verifyConnection")
		self.assertEqual(erpnext["blocks"][1]["bindings"], erpnext["blocks"][2]["bindings"])
		self.assertEqual(
			erpnext["blocks"][1]["fields"],
			["is_erpnext_in_different_site", "erpnext_site_url", "api_key", "api_secret", "erpnext_company"],
		)
		self.assertEqual(erpnext["blocks"][2]["component"], "productSync")
		self.assertEqual(
			erpnext["blocks"][2]["bindings"],
			{"settings": {"type": "Single", "doctype": "ERPNext CRM Settings"}},
		)
		self.assertEqual(erpnext["blocks"][2]["fields"], ["sync_products"])
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
				["erpnext", "verify-connection", "product-sync"],
			)

	def test_crm_ships_the_enrichment_pane_on_the_enrichment_settings_single(self):
		enrichment = self.pane("crm", "enrichment")
		block = enrichment["blocks"][0]

		self.assertEqual(len(enrichment["blocks"]), 1)
		self.assertEqual((block["key"], block["save_mode"]), ("general", "button"))
		self.assertEqual(block["binding"]["doctype"], "CRM Enrichment Settings")
		self.assertEqual(block["fields"], ["enabled", "auto_enrich", "max_pages"])
		self.assertEqual(block["roles"], ["Sales Manager", "System Manager"])

	def test_only_a_manager_sees_the_enrichment_pane(self):
		self.make_user(SALES_USER, "Sales User")
		self.make_user(SALES_MANAGER, "Sales Manager")

		with set_user(SALES_USER):
			self.assertIsNone(self.visible_pane("enrichment"))
		with set_user(SALES_MANAGER):
			self.assertEqual(
				[block["key"] for block in self.visible_pane("enrichment")["blocks"]], ["general"]
			)

	def test_the_whatsapp_pane_shows_only_where_frappe_whatsapp_is_installed(self):
		with self.whatsapp_installed(False):
			self.assertNotIn(("crm", "whatsapp"), self.pane_addresses())

		with self.whatsapp_installed(True):
			whatsapp = self.pane("crm", "whatsapp")

		self.assertEqual([block["key"] for block in whatsapp["blocks"]], ["whatsapp"])
		self.assertEqual(whatsapp["blocks"][0]["binding"]["doctype"], "WhatsApp Settings")
		self.assertNotIn("fields", whatsapp["blocks"][0])
		self.assertEqual(whatsapp["blocks"][0]["roles"], ["Sales Manager", "System Manager"])

	def whatsapp_installed(self, installed: bool):
		has_doctype = SettingsRules._has_doctype

		def fake(rules, doctype):
			return installed if doctype == "WhatsApp Settings" else has_doctype(rules, doctype)

		return patch.object(SettingsRules, "_has_doctype", autospec=True, side_effect=fake)

	def pane_addresses(self):
		return [(pane["app"], pane["key"]) for pane in resolve_panes()]

	def pane(self, app, key):
		return next(pane for pane in resolve_panes() if pane["app"] == app and pane["key"] == key)

	def sidebar_blocks(self, pane):
		"""The blocks CRM's sidebar lists under `pane` for the session user."""
		resolved = merge_settings()
		panes = SettingsFilter().filter(resolved.panes)["panes"]
		sidebar = filter_sidebar(resolved.sidebars["crm"], panes)
		entries = [entry for group in sidebar["groups"] for entry in group["panes"]]
		return next((entry["blocks"] for entry in entries if entry["pane"] == pane), [])

	def visible_pane(self, key, app="crm"):
		panes = SettingsFilter().filter(resolve_panes())["panes"]
		return next((pane for pane in panes if pane["app"] == app and pane["key"] == key), None)

	def make_user(self, email, role):
		if not frappe.db.exists("User", email):
			user = frappe.get_doc(doctype="User", email=email, first_name=role, send_welcome_email=0).insert(
				ignore_permissions=True
			)
			user.add_roles(role)
