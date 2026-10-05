# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import re

import frappe
from frappe import _
from frappe.model.document import Document


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

	def validate(self):
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
