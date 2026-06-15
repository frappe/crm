# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class CRMMergeLog(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		child_table_snapshot: DF.Code | None
		field_snapshot: DF.Code | None
		merged_at: DF.Datetime
		merged_by: DF.Link
		reference_doctype: DF.Link
		reference_snapshot: DF.Code | None
		source_document_name: DF.DynamicLink
		split_at: DF.Datetime | None
		split_by: DF.Link | None
		target_document_name: DF.DynamicLink
	# end: auto-generated types

	def before_insert(self):
		self.merged_at = frappe.utils.now()
		self.merged_by = frappe.session.user

	def validate(self):
		if not self.reference_doctype:
			frappe.throw(_("Reference DocType is required"))
		if not self.target_document_name:
			frappe.throw(_("Target Document Name is required"))
		if not self.source_document_name:
			frappe.throw(_("Source Document Name is required"))
		if self.target_document_name == self.source_document_name:
			frappe.throw(_("Target and Source documents cannot be the same"))
