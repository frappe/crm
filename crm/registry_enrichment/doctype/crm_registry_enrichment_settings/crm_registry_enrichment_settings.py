# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

# Bounds for the per-request timeout: a positive lower bound (a value below one second
# makes every lookup fail) and an upper bound so a long-queue worker cannot be pinned far
# beyond the intended limit. Mirrored by the defensive clamp in config/client.
MIN_REQUEST_TIMEOUT = 1
MAX_REQUEST_TIMEOUT = 60


class CRMRegistryEnrichmentSettings(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from crm.registry_enrichment.doctype.crm_registry_enrichment_field_mapping.crm_registry_enrichment_field_mapping import (
			CRMRegistryEnrichmentFieldMapping,
		)

		api_token: DF.Password | None
		auto_enrich: DF.Check
		enabled: DF.Check
		field_mappings: DF.Table[CRMRegistryEnrichmentFieldMapping]
		request_timeout: DF.Int
	# end: auto-generated types

	def validate(self):
		# A zero/empty value means "use the default", handled downstream. Any value that is
		# set must fall inside the supported band.
		if self.request_timeout and not (MIN_REQUEST_TIMEOUT <= self.request_timeout <= MAX_REQUEST_TIMEOUT):
			frappe.throw(
				_("Request Timeout must be between {0} and {1} seconds.").format(
					MIN_REQUEST_TIMEOUT, MAX_REQUEST_TIMEOUT
				),
				frappe.ValidationError,
			)
