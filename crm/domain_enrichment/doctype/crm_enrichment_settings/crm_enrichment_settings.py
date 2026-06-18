# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class CRMEnrichmentSettings(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from crm.domain_enrichment.doctype.crm_enrichment_domain.crm_enrichment_domain import (
			CRMEnrichmentDomain,
		)
		from crm.domain_enrichment.doctype.crm_enrichment_priority_keyword.crm_enrichment_priority_keyword import (
			CRMEnrichmentPriorityKeyword,
		)
		from crm.domain_enrichment.doctype.crm_enrichment_skip_pattern.crm_enrichment_skip_pattern import (
			CRMEnrichmentSkipPattern,
		)

		allow_private_networks: DF.Check
		allowed_domains: DF.Table[CRMEnrichmentDomain]
		blocked_domains: DF.Table[CRMEnrichmentDomain]
		enable_deal: DF.Check
		enable_lead: DF.Check
		enable_organization: DF.Check
		enabled: DF.Check
		max_depth: DF.Int
		max_download_bytes: DF.Int
		max_pages: DF.Int
		preview_max_pages: DF.Int
		preview_timeout: DF.Int
		priority_keywords: DF.Table[CRMEnrichmentPriorityKeyword]
		render_js: DF.Check
		request_timeout: DF.Int
		retry_count: DF.Int
		skip_patterns: DF.Table[CRMEnrichmentSkipPattern]
		user_agent: DF.Data | None
	# end: auto-generated types

	pass
