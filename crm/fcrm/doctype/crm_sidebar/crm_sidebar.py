# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import re

import frappe
from frappe import _
from frappe.model.document import Document

SITE_EDITOR_ROLES = ("System Manager", "Sales Manager")
OWN_ROWS_PER_LAYER = 50
OWN_KEY = re.compile(r"(site|user):[a-z0-9]{4,16}")


class CRMSidebar(Document):
	"""One layer of the CRM sidebar: the site's when `user` is blank, else that user's."""

	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from crm.fcrm.doctype.crm_sidebar_item.crm_sidebar_item import CRMSidebarItem

		items: DF.Table[CRMSidebarItem]
		user: DF.Link | None
	# end: auto-generated types

	def autoname(self):
		self.name = self.user or "Site"

	def validate(self):
		self.validate_keys()
		before = self.get_doc_before_save()
		stored = {row.key: row.link_to for row in before.items if row.added} if before else {}
		for row in self.items:
			if row.added:
				validate_added_row(row, stored.get(row.key))

	def validate_keys(self):
		"""Each key once; a row this layer adds has the layer's own key, and a layer adds at most 50."""
		keys = [row.key for row in self.items]
		if len(keys) != len(set(keys)):
			frappe.throw(_("A sidebar row is in this layer twice."))

		added = [row for row in self.items if row.added]
		if len(added) > OWN_ROWS_PER_LAYER:
			frappe.throw(_("You can add up to {0} rows to the sidebar.").format(OWN_ROWS_PER_LAYER))

		prefix = "user:" if self.user else "site:"
		for row in added:
			if not OWN_KEY.fullmatch(row.key) or not row.key.startswith(prefix):
				frappe.throw(_("{0} is not a key this layer can add.").format(row.key))


def validate_added_row(row, stored_link_to: str | None):
	"""A row a layer adds is a section or a DocType; a new or changed DocType is checked again."""
	if row.type == "Section":
		if not (row.label or "").strip():
			frappe.throw(_("Give the section a label."))
		row.link_type = row.link_to = row.icon = row.parent_key = None
		return

	if row.link_type != "DocType" or not row.link_to:
		frappe.throw(_("A row you add opens a DocType."))
	if row.link_to != stored_link_to:
		check_sidebar_doctype(row.link_to)
	row.label = row.label or row.link_to


def check_sidebar_doctype(doctype: str):
	"""A DocType can join the sidebar when it has a list, no built-in page opens it and the user reads it."""
	if not frappe.db.exists("DocType", doctype):
		frappe.throw(_("DocType {0} does not exist.").format(doctype))

	meta = frappe.get_meta(doctype)
	if meta.istable or meta.issingle or meta.is_virtual:
		frappe.throw(_("{0} cannot be in the sidebar: it has no list of records.").format(doctype))

	built_in = get_built_in_doctypes().get(doctype)
	if built_in:
		frappe.throw(_("{0} already opens {1}.").format(_(built_in), doctype))

	if not frappe.has_permission(doctype, "read"):
		frappe.throw(_("You cannot read {0}.").format(doctype), frappe.PermissionError)


def get_built_in_doctypes() -> dict[str, str]:
	"""The DocTypes a built-in page opens, with that page's label."""
	return {
		item["opens_doctype"]: item["label"]
		for item in frappe.get_hooks("standard_sidebar_items")
		if item.get("opens_doctype")
	}


def can_edit_site_sidebar(user: str | None = None) -> bool:
	"""Whether the user may change the sidebar everyone on the site starts from."""
	user = user or frappe.session.user
	return user == "Administrator" or bool(set(SITE_EDITOR_ROLES) & set(frappe.get_roles(user)))


def has_permission(doc, ptype=None, user=None) -> bool:
	"""A user's layer is theirs alone; the site layer is read by all and written by managers."""
	user = user or frappe.session.user
	if doc.user:
		return doc.user == user
	return ptype == "read" or can_edit_site_sidebar(user)


def get_permission_query_conditions(user=None) -> str:
	"""Each user lists their own layer and the site's; Administrator lists every layer."""
	user = user or frappe.session.user
	if user == "Administrator":
		return ""
	return f"(`tabCRM Sidebar`.user = {frappe.db.escape(user)} or coalesce(`tabCRM Sidebar`.user, '') = '')"


def delete_user_sidebar(doc, method=None):
	"""Drop a deleted user's layer, so its link does not block the delete."""
	if not frappe.db.table_exists("CRM Sidebar"):
		return
	for name in frappe.get_all("CRM Sidebar", filters={"user": doc.name}, pluck="name"):
		frappe.delete_doc("CRM Sidebar", name, ignore_permissions=True, delete_permanently=True)
