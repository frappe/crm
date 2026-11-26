# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

SITE_EDITOR_ROLES = ("System Manager", "Sales Manager")


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
	for name in frappe.get_all("CRM Sidebar", filters={"user": doc.name}, pluck="name"):
		frappe.delete_doc("CRM Sidebar", name, ignore_permissions=True, delete_permanently=True)
