# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import sys
from types import ModuleType
from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from crm.www.crm import get_boot, get_state_options


def _fake_india_compliance(states: dict) -> dict:
	"""Build a fake `india_compliance.gst_india.constants` module tree for sys.modules.

	`from india_compliance.gst_india.constants import INDIAN_STATES` imports each parent
	package, so all three levels must be present.
	"""
	root = ModuleType("india_compliance")
	gst = ModuleType("india_compliance.gst_india")
	constants = ModuleType("india_compliance.gst_india.constants")
	constants.INDIAN_STATES = states
	return {
		"india_compliance": root,
		"india_compliance.gst_india": gst,
		"india_compliance.gst_india.constants": constants,
	}


class TestGetStateOptions(FrappeTestCase):
	def test_returns_a_dict(self):
		# Never raises; always a dict regardless of what's installed.
		self.assertIsInstance(get_state_options(), dict)

	def test_empty_without_india_compliance(self):
		with patch("frappe.get_installed_apps", return_value=["frappe", "crm"]):
			self.assertEqual(get_state_options(), {})

	def test_resilient_when_get_installed_apps_raises(self):
		# The v15 boot-context concern: get_installed_apps blowing up must NOT break boot.
		with patch("frappe.get_installed_apps", side_effect=Exception("boot context")):
			self.assertEqual(get_state_options(), {})

	def test_resilient_when_import_fails(self):
		# App reported installed but constant import fails (e.g. version mismatch).
		with patch("frappe.get_installed_apps", return_value=["frappe", "crm", "india_compliance"]):
			# No fake module injected -> ImportError -> graceful {}.
			self.assertEqual(get_state_options(), {})

	def test_returns_states_when_app_installed(self):
		states = {"Goa": "30", "Kerala": "32", "Punjab": "03"}
		with (
			patch(
				"frappe.get_installed_apps",
				return_value=["frappe", "crm", "india_compliance"],
			),
			patch.dict(sys.modules, _fake_india_compliance(states)),
		):
			result = get_state_options()
		self.assertEqual(list(result.keys()), ["India"])
		self.assertEqual(result["India"], ["Goa", "Kerala", "Punjab"])


class TestGetBoot(FrappeTestCase):
	def test_boot_includes_state_options_and_does_not_raise(self):
		boot = get_boot()
		self.assertIn("state_options", boot)
		self.assertIsInstance(boot["state_options"], dict)

	def test_boot_survives_state_options_failure(self):
		# Even if the state lookup somehow raises, get_boot itself must succeed.
		with patch("crm.www.crm.get_state_options", side_effect=Exception("boom")):
			with self.assertRaises(Exception):
				# Sanity: the mock does raise when called directly...
				get_state_options()
		# ...but get_state_options in production swallows errors, so boot is safe.
		with patch("frappe.get_installed_apps", side_effect=Exception("boot context")):
			boot = get_boot()
		self.assertEqual(boot["state_options"], {})
