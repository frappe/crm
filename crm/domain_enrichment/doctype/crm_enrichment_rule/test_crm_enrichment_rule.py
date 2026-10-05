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

	def _rule(self, pattern="acme", is_regex=1, rule_type="Social", target=None):
		# Seeded rules already cover the real networks/industries, so default to a fresh target.
		target = target or f"test {frappe.generate_hash(length=6)}"
		if rule_type == "Industry" and not frappe.db.exists("CRM Industry", target):
			frappe.get_doc({"doctype": "CRM Industry", "industry": target}).insert()
		return frappe.get_doc(
			{
				"doctype": "CRM Enrichment Rule",
				"rule_type": rule_type,
				"target_value": target if rule_type == "Social" else None,
				"industry": target if rule_type == "Industry" else None,
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

	def test_rule_name_is_built_from_target(self):
		social = self._rule(target="mastodon test").insert()
		self.assertEqual(social.rule_name, "Social: mastodon test")
		industry = self._rule(rule_type="Industry", target="Test Industry").insert()
		self.assertEqual(industry.rule_name, "Industry: Test Industry")

	def test_rule_name_follows_target_change(self):
		rule = self._rule(target="old platform").insert()
		rule.target_value = "new platform"
		rule.save()
		self.assertEqual(rule.rule_name, "Social: new platform")

	def test_duplicate_target_is_rejected(self):
		self._rule(target="dup platform").insert()
		with self.assertRaises(frappe.DuplicateEntryError):
			self._rule(target="Dup Platform").insert()

	def test_same_target_in_other_rule_type_is_allowed(self):
		self._rule(target="Shared Target").insert()
		self._rule(rule_type="Industry", target="Shared Target").insert()

	def test_missing_target_is_rejected(self):
		rule = self._rule()
		rule.target_value = None
		with self.assertRaises(frappe.ValidationError):
			rule.insert()

	def test_resave_unchanged_rule_is_allowed(self):
		# The duplicate check must exclude the rule itself.
		rule = self._rule(target="resave platform").insert()
		rule.save()

	def test_editing_target_onto_other_rule_is_rejected(self):
		self._rule(target="taken platform").insert()
		rule = self._rule(target="free platform").insert()
		rule.target_value = "Taken Platform"
		with self.assertRaises(frappe.DuplicateEntryError):
			rule.save()

	def test_target_whitespace_is_stripped(self):
		rule = self._rule(target=" spaced ").insert()
		self.assertEqual(rule.target_value, "spaced")
		self.assertEqual(rule.rule_name, "Social: spaced")
