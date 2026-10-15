# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

# Field Mapping only targets the three app-owned CRM doctypes that can be enriched.
ALLOWED_TARGET_DOCTYPES = ("CRM Lead", "CRM Deal", "CRM Organization")


class CRMEnrichmentFieldMapping(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		create_missing_link: DF.Check
		default_values: DF.SmallText | None
		enabled: DF.Check
		source_key: DF.Literal[
			"company_name",
			"description",
			"logo",
			"industry",
			"primary_email",
			"primary_phone",
			"secondary_phone",
			"linkedin",
			"twitter",
			"github",
			"facebook",
			"instagram",
			"youtube",
		]
		target_doctype: DF.Link
		target_fieldname: DF.Data
		write_policy: DF.Literal["Fill if empty", "Always refresh", "Override defaults"]
	# end: auto-generated types

	def validate(self):
		if self.target_doctype not in ALLOWED_TARGET_DOCTYPES:
			frappe.throw(_("Target Doctype must be one of: {0}").format(", ".join(ALLOWED_TARGET_DOCTYPES)))
		if not frappe.get_meta(self.target_doctype).has_field(self.target_fieldname):
			frappe.throw(_("{0} has no field {1}").format(self.target_doctype, self.target_fieldname))
