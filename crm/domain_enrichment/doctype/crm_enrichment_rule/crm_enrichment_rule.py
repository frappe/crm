# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

# import frappe
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

	pass
