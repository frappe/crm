# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class CRMEnrichmentRun(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		company_name: DF.Data | None
		emails_found: DF.Int
		finished_on: DF.Datetime | None
		industry: DF.Data | None
		industry_confidence: DF.Float
		notes: DF.SmallText | None
		phones_found: DF.Int
		raw_json: DF.Code | None
		reference_doctype: DF.Link | None
		reference_name: DF.DynamicLink | None
		social_profiles: DF.SmallText | None
		source_website: DF.Data | None
		started_on: DF.Datetime | None
		status: DF.Literal["Queued", "Running", "Completed", "Failed"]
	# end: auto-generated types

	pass
