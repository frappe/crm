# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class CRMRegistryEnrichmentRun(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		document_number: DF.Data | None
		error: DF.SmallText | None
		fields_updated: DF.Int
		finished_at: DF.Datetime | None
		raw_json: DF.Code | None
		reference_doctype: DF.Link | None
		reference_name: DF.DynamicLink | None
		started_at: DF.Datetime | None
		status: DF.Literal["Queued", "Running", "Completed", "Failed"]
	# end: auto-generated types

	pass
