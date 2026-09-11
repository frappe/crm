# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class CRMLeadSegmentLeads(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		lead: DF.Link
		lead_name: DF.Data | None
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
	# end: auto-generated types

	pass


def on_doctype_update():
	# A lead belongs to a segment at most once, but may belong to many segments, so the
	# constraint is on the pair. `unique` on the `lead` field alone would make it unique
	# across the whole table, letting a lead join only one segment ever.
	frappe.db.add_unique("CRM Lead Segment Leads", ("parent", "lead"), constraint_name="unique_segment_lead")
