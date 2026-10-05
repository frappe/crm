# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import re

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.query_builder.functions import Lower


def get_target_field(rule_type):
	return "target_value" if rule_type == "Social" else "industry"


def find_duplicate(rule_type, target, exclude=None):
	field = get_target_field(rule_type)
	Rule = frappe.qb.DocType("CRM Enrichment Rule")
	query = (
		frappe.qb.from_(Rule)
		.select(Rule.name)
		.where((Rule.rule_type == rule_type) & (Lower(Rule[field]) == target.lower()))
	)
	if exclude:
		query = query.where(Rule.name != exclude)
	return query.limit(1).run(pluck=True)


class CRMEnrichmentRule(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from crm.domain_enrichment.doctype.crm_enrichment_rule_pattern.crm_enrichment_rule_pattern import (
			CRMEnrichmentRulePattern,
		)

		enabled: DF.Check
		industry: DF.Link | None
		match_scope: DF.Literal["Headline", "Full Text", "HTML", "Headers", "URL"]
		patterns: DF.Table[CRMEnrichmentRulePattern]
		rule_name: DF.Data
		rule_type: DF.Literal["Industry", "Social"]
		target_value: DF.Data | None
		weight: DF.Float
	# end: auto-generated types

	def before_validate(self):
		field = get_target_field(self.rule_type)
		self.set(field, (self.get(field) or "").strip() or None)
		self.rule_name = f"{self.rule_type}: {self.get_target()}"

	def get_target(self):
		return self.get(get_target_field(self.rule_type))

	def validate(self):
		self.validate_target()
		self.validate_duplicate()
		self.validate_patterns()

	def validate_target(self):
		if not self.get_target():
			label = _("Target Value") if self.rule_type == "Social" else _("Industry")
			frappe.throw(_("{0} is required for {1} rules").format(label, _(self.rule_type)))

	def validate_duplicate(self):
		if find_duplicate(self.rule_type, self.get_target(), exclude=self.name):
			frappe.throw(
				_("A {0} rule for {1} already exists").format(_(self.rule_type), self.get_target()),
				frappe.DuplicateEntryError,
			)

	def validate_patterns(self):
		# The crawler compiles regex patterns with Python's `re` and skips any that
		# fail (config._compile_pattern), so a bad one would save fine and then
		# silently never match. Reject it here, against the engine that runs it.
		for row in self.patterns:
			if not row.is_regex:
				continue
			try:
				re.compile(row.pattern, re.IGNORECASE)
			except re.error as e:
				frappe.throw(_("Row #{0}: Not a valid regular expression: {1}").format(row.idx, str(e)))
