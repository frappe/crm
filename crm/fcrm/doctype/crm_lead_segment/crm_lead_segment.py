# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document, get_controller

from crm.api.session import CRM_ALLOWED_ROLES


class CRMLeadSegment(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from crm.fcrm.doctype.crm_lead_segment_leads.crm_lead_segment_leads import CRMLeadSegmentLeads

		assigned_to: DF.Link | None
		description: DF.TextEditor | None
		leads: DF.Table[CRMLeadSegmentLeads]
		segment_name: DF.Data
	# end: auto-generated types

	def validate(self):
		self.validate_assigned_to()
		self.validate_unique_leads()

	def validate_assigned_to(self):
		if not self.assigned_to or self.assigned_to == "Administrator":
			return

		if not frappe.db.exists(
			"Has Role", {"parenttype": "User", "parent": self.assigned_to, "role": ["in", CRM_ALLOWED_ROLES]}
		):
			frappe.throw(
				_("{0} is not a CRM user and cannot be assigned a segment.").format(
					frappe.bold(self.assigned_to)
				)
			)

	def validate_unique_leads(self):
		# The (parent, lead) unique index is the real guarantee. This runs first only so the
		# user is told which lead is duplicated — Frappe's own unique-violation handler maps a
		# composite index back to its first column and would report "Parent must be unique".
		seen = set()
		for row in self.leads:
			if row.lead in seen:
				frappe.throw(
					_("Lead {0} is already in this segment.").format(frappe.bold(row.lead_name or row.lead))
				)
			seen.add(row.lead)

	@staticmethod
	def default_list_data():
		columns = [
			{
				"label": "Segment Name",
				"type": "Data",
				"key": "segment_name",
				"width": "16rem",
			},
			{
				"label": "Assigned To",
				"type": "Link",
				"key": "assigned_to",
				"options": "User",
				"width": "12rem",
			},
			{
				"label": "Description",
				"type": "Text Editor",
				"key": "description",
				"width": "16rem",
			},
			{
				"label": "Last Modified",
				"type": "Datetime",
				"key": "modified",
				"width": "8rem",
			},
		]
		rows = [
			"name",
			"segment_name",
			"assigned_to",
			"description",
			"creation",
			"modified",
		]
		return {"columns": columns, "rows": rows}


def get_segment_for_write(segment: str):
	"""Return the segment doc, or throw if the user cannot write to it."""
	if not frappe.has_permission("CRM Lead Segment", "write", segment):
		frappe.throw(_("Not allowed to modify this segment"), frappe.PermissionError)

	# Deliberately not get_cached_doc: the child table would be cached along with the doc.
	return frappe.get_doc("CRM Lead Segment", segment)


@frappe.whitelist()
def add_leads(segment: str, leads: str | list) -> dict:
	"""Add leads to a segment, skipping ones already in it or not readable by the user.

	Duplicates are filtered rather than left to the unique index, which would abort the
	whole save and take the valid leads of the batch down with it.
	"""
	leads = frappe.parse_json(leads)
	if not isinstance(leads, list):
		frappe.throw(_("Leads must be a list"))

	doc = get_segment_for_write(segment)
	existing = {row.lead for row in doc.leads}

	# dict.fromkeys also collapses a lead repeated within the incoming batch, which would
	# otherwise be appended twice and trip validate_unique_leads.
	candidates = list(dict.fromkeys(lead for lead in leads if lead not in existing))

	# One query for the whole batch: get_list applies the CRM Lead permission query
	# conditions, so unreadable and non-existent leads drop out together.
	readable = set()
	if candidates:
		readable = set(frappe.get_list("CRM Lead", filters={"name": ["in", candidates]}, pluck="name"))

	added = 0
	for lead in candidates:
		if lead not in readable:
			continue
		doc.append("leads", {"lead": lead})
		added += 1

	if added:
		doc.save()

	return {"added": added, "skipped": len(leads) - added, "total": len(doc.leads)}


@frappe.whitelist()
def remove_leads(segment: str, leads: str | list) -> dict:
	"""Remove leads from a segment."""
	leads = frappe.parse_json(leads)
	if not isinstance(leads, list):
		frappe.throw(_("Leads must be a list"))

	doc = get_segment_for_write(segment)

	before = len(doc.leads)
	doc.leads = [row for row in doc.leads if row.lead not in set(leads)]
	removed = before - len(doc.leads)

	if removed:
		doc.save()

	return {"removed": removed, "total": len(doc.leads)}


@frappe.whitelist()
def get_segment_leads(
	segment: str, start: int = 0, page_length: int = 20, order_by: str = "modified desc"
) -> dict:
	"""Return one page of a segment's leads, with the standard CRM Lead list columns."""
	if not frappe.has_permission("CRM Lead Segment", "read", segment):
		frappe.throw(_("Not allowed to read this segment"), frappe.PermissionError)

	list_data = get_controller("CRM Lead").default_list_data()

	names = frappe.get_all(
		"CRM Lead Segment Leads",
		filters={"parent": segment, "parenttype": "CRM Lead Segment"},
		pluck="lead",
	)

	data = []
	if names:
		data = frappe.get_list(
			"CRM Lead",
			filters={"name": ["in", names]},
			fields=list_data.get("rows"),
			order_by=order_by,
			offset=start,
			limit=page_length,
		)

	return {
		"data": data,
		"columns": list_data.get("columns"),
		"total_count": len(names),
		"row_count": len(data),
	}
