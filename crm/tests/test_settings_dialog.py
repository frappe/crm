# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

import json
import os
from unittest.mock import patch

import frappe
from frappe.shell.settings import resolve_panes
from frappe.tests import IntegrationTestCase

RECORDS = ("crm", "crm-frappe")


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
			[("deals", "button"), ("communication", "auto"), ("activity-timeline", "auto")],
		)
		self.assertTrue(all(block["binding"]["doctype"] == "FCRM Settings" for block in general["blocks"]))

	def test_crm_adds_a_telephony_block_to_desks_profile_pane(self):
		profile = self.pane("frappe", "profile")
		telephony = next(block for block in profile["blocks"] if block["key"] == "telephony")

		self.assertEqual(telephony["app"], "crm")
		self.assertEqual(telephony["binding"]["doctype"], "CRM Telephony Agent")
		self.assertEqual(telephony["binding"]["resolver"], "session_user")

	def pane(self, app, key):
		return next(pane for pane in resolve_panes() if pane["app"] == app and pane["key"] == key)
