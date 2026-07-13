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
		with patch("crm.www.crm.get_installed_apps", return_value=["frappe", "crm"]):
			self.assertEqual(get_state_options(), {})

	def test_resilient_when_get_installed_apps_raises(self):
		# The v15 boot-context concern: get_installed_apps blowing up must NOT break boot.
		with patch("crm.www.crm.get_installed_apps", side_effect=Exception("boot context")):
			self.assertEqual(get_state_options(), {})

	def test_resilient_when_import_fails(self):
		# App reported installed but the constant import fails (e.g. version mismatch).
		# Inject a constants module lacking INDIAN_STATES so the import fails deterministically,
		# regardless of whether india_compliance is actually importable in this environment.
		broken = _fake_india_compliance({})
		del broken["india_compliance.gst_india.constants"].INDIAN_STATES
		with (
			patch("crm.www.crm.get_installed_apps", return_value=["frappe", "crm", "india_compliance"]),
			patch.dict(sys.modules, broken),
		):
			self.assertEqual(get_state_options(), {})

	def test_returns_states_when_app_installed(self):
		states = {"Goa": "30", "Kerala": "32", "Punjab": "03"}
		with (
			patch(
				"crm.www.crm.get_installed_apps",
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

	def test_boot_degrades_when_state_lookup_fails(self):
		# The v15 boot-context concern: if the state lookup misbehaves, get_boot must still
		# succeed and state_options must be an empty map (never break page load). Patch only
		# the binding used by get_state_options — patching frappe.get_installed_apps globally
		# would break unrelated earlier boot steps (get_translated_doctypes resolves hooks via
		# get_installed_apps), which is what made this test fail in CI.
		with patch("crm.www.crm.get_installed_apps", side_effect=Exception("boot context")):
			boot = get_boot()
		self.assertEqual(boot["state_options"], {})
