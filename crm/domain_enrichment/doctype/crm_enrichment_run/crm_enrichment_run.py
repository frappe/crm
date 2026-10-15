# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cast, cstr, now_datetime

from crm.permissions.org_hierarchy import _permission_query_conditions


class CRMEnrichmentRun(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from crm.domain_enrichment.doctype.crm_enrichment_run_change.crm_enrichment_run_change import (
			CRMEnrichmentRunChange,
		)

		changes: DF.Table[CRMEnrichmentRunChange]
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
		status: DF.Literal["Queued", "Running", "Completed", "Failed", "Reverted"]
		undone_by: DF.Link | None
		undone_on: DF.Datetime | None
	# end: auto-generated types

	def undo(self) -> dict:
		"""Revert the field values this run wrote to its reference record.

		A field is reverted only while the record still holds the value this run
		wrote (compared as strings, like ``write_run``, after casting the stored
		value to the field's type); a field the user has edited since is skipped.
		The record is saved with a normal ``save()`` so permissions and validation
		run. Link masters the run created are left in place.

		Returns ``{reverted: [fieldname, ...], skipped: [fieldname, ...]}``.
		"""
		# Re-read the status under a row lock so two concurrent undos cannot both pass.
		status = frappe.db.get_value(self.doctype, self.name, "status", for_update=True)
		if status != "Completed":
			frappe.throw(_("Only a completed enrichment run can be undone."), frappe.ValidationError)
		if not self.changes:
			frappe.throw(_("This enrichment run did not change any fields."), frappe.ValidationError)

		record = frappe.get_doc(self.reference_doctype, self.reference_name)
		reverted, skipped = [], []
		for change in self.changes:
			df = record.meta.get_field(change.fieldname)
			# Cast first so a numeric field's 9000.0 matches its stored "9000".
			if not df or cstr(record.get(change.fieldname)) != cstr(restore_value(df, change.new_value)):
				skipped.append(change.fieldname)
				continue
			record.set(change.fieldname, restore_value(df, change.old_value))
			reverted.append(change.fieldname)

		if reverted:
			record.save()

		self.db_set({"status": "Reverted", "undone_on": now_datetime(), "undone_by": frappe.session.user})
		return {"reverted": reverted, "skipped": skipped}


def restore_value(df, value):
	"""Cast a value stored as text on a Change row back to the field's type; empty
	restores as None."""
	if value is None or value == "":
		return None
	return cast(df.fieldtype, value)


def get_permission_query_conditions(user=None):
	"""Limit runs to those whose lead or deal the user can see."""
	user = user or frappe.session.user
	Run = frappe.qb.DocType("CRM Enrichment Run")
	restricted, visible = [], None
	for doctype in ("CRM Lead", "CRM Deal"):
		conditions = _permission_query_conditions(user, doctype)
		if not conditions:
			continue
		restricted.append(doctype)
		DT = frappe.qb.DocType(doctype)
		criterion = (Run.reference_doctype == doctype) & Run.reference_name.isin(
			frappe.qb.from_(DT).select(DT.name).where(conditions)
		)
		visible = criterion if visible is None else visible | criterion

	if not restricted:
		return ""
	visible = Run.reference_doctype.notin(restricted) | visible
	return visible.get_sql(with_namespace=True, quote_char="`", secondary_quote_char="'")


def has_permission(doc, ptype, user):
	if ptype == "create" or not (doc.reference_doctype and doc.reference_name):
		return True
	return frappe.has_permission(doc.reference_doctype, "read", doc=doc.reference_name, user=user)
