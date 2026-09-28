# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

from crm.domain_enrichment.config import MAX_PAGES_LIMIT


class CRMEnrichmentSettings(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from crm.domain_enrichment.doctype.crm_enrichment_domain.crm_enrichment_domain import (
			CRMEnrichmentDomain,
		)
		from crm.domain_enrichment.doctype.crm_enrichment_link_priority.crm_enrichment_link_priority import (
			CRMEnrichmentLinkPriority,
		)
		from crm.domain_enrichment.doctype.crm_enrichment_skip_pattern.crm_enrichment_skip_pattern import (
			CRMEnrichmentSkipPattern,
		)

		allowed_domains: DF.Table[CRMEnrichmentDomain]
		auto_enrich: DF.Check
		blocked_domains: DF.Table[CRMEnrichmentDomain]
		enabled: DF.Check
		link_priority_order: DF.Table[CRMEnrichmentLinkPriority]
		max_depth: DF.Int
		max_download_bytes: DF.Int
		max_pages: DF.Int
		request_timeout: DF.Int
		retry_count: DF.Int
		skip_patterns: DF.Table[CRMEnrichmentSkipPattern]
		user_agent: DF.Data | None
	# end: auto-generated types

	def validate(self):
		self.validate_max_pages()

	def validate_max_pages(self):
		"""Keep the page budget inside 1..MAX_PAGES_LIMIT.

		An empty value is left alone: config._setting falls back to
		DEFAULT_SETTINGS["max_pages"] for an unsaved Single, and rejecting a blank
		here would block saving any other field on a fresh site.
		"""
		if self.max_pages in (None, ""):
			return

		if int(self.max_pages) < 1 or int(self.max_pages) > MAX_PAGES_LIMIT:
			frappe.throw(
				_("Max Pages must be a whole number between 1 and {0}").format(MAX_PAGES_LIMIT),
				title=_("Invalid Max Pages"),
			)
