# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase

# On IntegrationTestCase, the doctype test records and all
# link-field test record dependencies are recursively loaded
# Use these module variables to add/remove to/from that list
EXTRA_TEST_RECORD_DEPENDENCIES = []  # eg. ["User"]
IGNORE_TEST_RECORD_DEPENDENCIES = []  # eg. ["User"]


class IntegrationTestCRMEnrichmentRule(IntegrationTestCase):
	"""
	Integration tests for CRMEnrichmentRule.
	Use this class for testing interactions between multiple components.
	"""

	def _rule(self, pattern, is_regex=1):
		return frappe.get_doc(
			{
				"doctype": "CRM Enrichment Rule",
				"rule_name": f"Social: test {frappe.generate_hash(length=6)}",
				"rule_type": "Social",
				"target_value": "linkedin",
				"match_scope": "HTML",
				"patterns": [{"pattern": pattern, "is_regex": is_regex}],
			}
		)

	def test_invalid_regex_is_rejected(self):
		with self.assertRaises(frappe.ValidationError):
			self._rule("linkedin\\.com/(company").insert()

	def test_python_only_regex_is_accepted(self):
		# Named groups in Python's syntax; JavaScript's RegExp rejects this.
		self._rule(r"linkedin\.com/company/(?P<slug>[\w-]+)").insert()

	def test_substring_pattern_is_not_compiled(self):
		# is_regex=0 patterns are escaped by the crawler, so "(" is just a character.
		self._rule("acme (", is_regex=0).insert()
