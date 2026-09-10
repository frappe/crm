# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


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

	pass
