# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Pure unit tests for config-layer pattern compilation (``config._compile_pattern``).

Fully offline: no DB, no network. Covers the word-boundary fix -- an un-anchored
short substring keyword like "erp" or "api" previously matched inside unrelated
words ("waterproofing", "capital"), causing false industry-classification hits.
"""

from __future__ import annotations

from unittest.mock import patch

import frappe
from frappe.tests import UnitTestCase

from crm.domain_enrichment.config import _compile_pattern, enabled_doctypes


class CompilePatternTest(UnitTestCase):
	def test_substring_pattern_does_not_match_inside_unrelated_word(self):
		erp_rx = _compile_pattern("erp", is_regex=0)
		self.assertIsNone(erp_rx.search("Industrial Adhesives, Paints and Waterproofing Solutions"))
		self.assertIsNone(erp_rx.search("enterprise value creation"))

	def test_substring_pattern_still_matches_standalone_word(self):
		erp_rx = _compile_pattern("erp", is_regex=0)
		self.assertIsNotNone(erp_rx.search("Our ERP rollout finished on schedule"))

	def test_api_pattern_does_not_match_inside_capital_or_rapid(self):
		api_rx = _compile_pattern("api", is_regex=0)
		self.assertIsNone(api_rx.search("venture capital and rapid growth"))
		self.assertIsNotNone(api_rx.search("a public REST API for developers"))

	def test_multi_word_phrase_pattern_still_matches(self):
		rx = _compile_pattern("enterprise resource planning", is_regex=0)
		self.assertIsNotNone(rx.search("our Enterprise Resource Planning suite"))

	def test_is_regex_patterns_are_left_unanchored(self):
		# An admin-authored regex (is_regex=1) is compiled as-is -- no word-boundary
		# wrapping, so existing admin patterns (e.g. social-profile URL regexes) keep
		# their exact intended behavior.
		rx = _compile_pattern(r"linkedin\.com/(company|in|school)/", is_regex=1)
		self.assertIsNotNone(rx.search("https://www.linkedin.com/company/acme"))


class EnabledDoctypesTest(UnitTestCase):
	def enabled_with(self, **settings):
		with patch("crm.domain_enrichment.config.get_settings", return_value=frappe._dict(settings)):
			return enabled_doctypes()

	def test_unsaved_settings_enable_every_doctype(self):
		self.assertEqual(self.enabled_with(), ["CRM Lead", "CRM Deal", "CRM Organization"])

	def test_a_doctype_switched_off_is_left_out(self):
		self.assertEqual(self.enabled_with(enabled=1, enable_deal=0), ["CRM Lead", "CRM Organization"])

	def test_the_master_switch_turns_every_doctype_off(self):
		self.assertEqual(self.enabled_with(enabled=0, enable_lead=1, enable_deal=1), [])
