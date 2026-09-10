# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

# Field Mapping only targets the phase-1 CRM doctypes that can be enriched.
ALLOWED_TARGET_DOCTYPES = ("CRM Organization", "CRM Lead")


class CRMRegistryEnrichmentFieldMapping(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		create_missing_link: DF.Check
		enabled: DF.Check
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		source_key: DF.Literal[
			"legal_name",
			"trade_name",
			"tax_id",
			"registration_status",
			"registration_status_date",
			"opening_date",
			"legal_nature",
			"company_size",
			"share_capital",
			"tax_regime",
			"simples_nacional",
			"industry",
			"industry_section",
			"email",
			"phone",
			"mobile_no",
			"address",
		]
		target_doctype: DF.Literal["CRM Organization", "CRM Lead"]
		target_fieldname: DF.Data
		write_policy: DF.Literal["Fill if empty", "Always refresh"]
	# end: auto-generated types

	def validate(self):
		if self.target_doctype not in ALLOWED_TARGET_DOCTYPES:
			frappe.throw(_("Target Doctype must be one of: {0}").format(", ".join(ALLOWED_TARGET_DOCTYPES)))
		if not frappe.get_meta(self.target_doctype).has_field(self.target_fieldname):
			frappe.throw(_("{0} has no field {1}").format(self.target_doctype, self.target_fieldname))
