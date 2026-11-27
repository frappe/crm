# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import escape_html, get_fullname

from crm.api.comment import extract_mentions
from crm.fcrm.doctype.crm_notification.crm_notification import notify_user

# Notes on these doctypes are as visible as the record they belong to.
PERMISSIONED_REFERENCES = ("CRM Lead", "CRM Deal")


class FCRMNote(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		content: DF.TextEditor | None
		pinned: DF.Check
		pinned_by: DF.Link | None
		pinned_on: DF.Datetime | None
		reference_docname: DF.DynamicLink | None
		reference_doctype: DF.Link | None
		title: DF.Data
	# end: auto-generated types

	@staticmethod
	def default_list_data():
		rows = [
			"name",
			"title",
			"content",
			"reference_doctype",
			"reference_docname",
			"owner",
			"modified",
		]
		return {"columns": [], "rows": rows}

	def on_update(self):
		self.notify_mentions()

	def notify_mentions(self):
		"""Notify people mentioned in the note, once, when they are first added."""
		if self.reference_doctype not in PERMISSIONED_REFERENCES or not self.reference_docname:
			return

		before = self.get_doc_before_save()
		already_mentioned = {m.email for m in extract_mentions(before.content)} if before else set()
		mentioned = {m.email for m in extract_mentions(self.content)} - already_mentioned
		if mentioned:
			# a mention removed and added back later shouldn't notify the same person again
			mentioned -= set(
				frappe.get_all(
					"CRM Notification",
					filters={
						"type": "Mention",
						"notification_type_doctype": "FCRM Note",
						"notification_type_doc": self.name,
						"to_user": ("in", list(mentioned)),
					},
					pluck="to_user",
				)
			)
		# the notification carries the note, so it only goes to people who can read the record
		mentioned = {
			email
			for email in mentioned
			if can_read_reference(self.reference_doctype, self.reference_docname, email)
		}
		if not mentioned:
			return

		is_lead = self.reference_doctype == "CRM Lead"
		record = frappe.db.get_value(
			self.reference_doctype,
			self.reference_docname,
			["lead_name"] if is_lead else ["organization", "lead_name"],
			as_dict=True,
		)
		name = (record.lead_name if is_lead else record.organization or record.lead_name) if record else ""
		author = get_fullname(frappe.session.user)
		notification_text = f"""
			<div class="mb-2 leading-5 text-ink-gray-5">
				<span class="font-medium text-ink-gray-9">{escape_html(author)}</span>
				<span>{_("mentioned you in a note on {0}").format(_("lead") if is_lead else _("deal"))}</span>
				<span class="font-medium text-ink-gray-9">{escape_html(name or self.reference_docname)}</span>
			</div>
		"""

		for email in mentioned:
			notify_user(
				{
					"owner": frappe.session.user,
					"assigned_to": email,
					"notification_type": "Mention",
					"message": self.content,
					"notification_text": notification_text,
					"reference_doctype": "FCRM Note",
					"reference_docname": self.name,
					"redirect_to_doctype": self.reference_doctype,
					"redirect_to_docname": self.reference_docname,
				}
			)


def get_permission_query_conditions(user=None):
	"""List a note on a lead or deal only if the user can read that record."""
	user = user or frappe.session.user
	if user == "Administrator":
		return ""

	conditions = [
		"coalesce(`tabFCRM Note`.`reference_docname`, '') = ''",
		"coalesce(`tabFCRM Note`.`reference_doctype`, '') not in ({})".format(
			", ".join(frappe.db.escape(doctype) for doctype in PERMISSIONED_REFERENCES)
		),
	]
	for doctype in PERMISSIONED_REFERENCES:
		if not frappe.has_permission(doctype, "read", user=user):
			continue
		# get_list covers roles, user permissions, shares and the permission hooks of the record
		readable = frappe.get_list(
			doctype, fields=["name"], limit_page_length=0, order_by="", user=user, run=0
		)
		conditions.append(
			f"(`tabFCRM Note`.`reference_doctype` = {frappe.db.escape(doctype)}"
			f" and `tabFCRM Note`.`reference_docname` in ({readable}))"
		)
	return "({})".format(" or ".join(conditions))


def has_permission(doc, ptype=None, user=None):
	"""Allow a note on a lead or deal only if the user can read that record."""
	user = user or frappe.session.user
	if user == "Administrator":
		return True

	references = {(doc.reference_doctype, doc.reference_docname)}
	# a save is checked with the new values, so moving a note also needs access to where it was
	saved = doc.name and frappe.db.get_value(
		"FCRM Note", doc.name, ["reference_doctype", "reference_docname"]
	)
	if saved:
		references.add(tuple(saved))

	return all(can_read_reference(*reference, user) for reference in references)


def can_read_reference(doctype, name, user):
	if doctype not in PERMISSIONED_REFERENCES or not name:
		return True
	return bool(frappe.db.exists(doctype, name)) and frappe.has_permission(doctype, "read", name, user=user)


@frappe.whitelist()
def set_pinned(name: str, pinned: bool):
	"""Pin or unpin a note without changing when it was last edited."""
	note = frappe.get_doc("FCRM Note", name)
	note.check_permission("write")
	if bool(note.pinned) == bool(pinned):
		return

	frappe.db.set_value(
		"FCRM Note",
		name,
		{
			"pinned": int(pinned),
			"pinned_by": frappe.session.user if pinned else None,
			"pinned_on": frappe.utils.now() if pinned else None,
		},
		update_modified=False,
	)
	# keep a history entry (shown on the lead or deal timeline) without changing "last edited"
	frappe.get_doc(
		{
			"doctype": "Version",
			"ref_doctype": "FCRM Note",
			"docname": name,
			"data": frappe.as_json({"changed": [["pinned", int(note.pinned), int(pinned)]]}),
		}
	).insert(ignore_permissions=True)
