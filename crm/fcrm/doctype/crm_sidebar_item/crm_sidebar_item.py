# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

DEFAULT_DOCTYPE_ICON = "file-text"
BOOT_FIELDS = ("name1", "label", "type", "route", "dt", "icon")


class CRMSidebarItem(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		dt: DF.Link | None
		hidden: DF.Check
		icon: DF.Data | None
		is_standard: DF.Check
		label: DF.Data | None
		name1: DF.Data | None
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		route: DF.Data | None
		type: DF.Literal["Page", "DocType"]
	# end: auto-generated types

	def set_standard(self, standard_item: dict):
		"""The hook owns a built-in page's type and route; the admin owns the rest."""
		self.type = "Page"
		self.route = standard_item.get("route")
		self.dt = None

	def validate_doctype(self, is_new: bool):
		if self.type != "DocType":
			frappe.throw(_("Row {0}: only DocType items can be added to the sidebar.").format(self.idx))
		if not self.dt:
			frappe.throw(_("Row {0}: choose a DocType.").format(self.idx))
		# A DocType that later turns single or virtual stays until an admin removes it.
		if is_new:
			self.validate_has_list()

		self.route = None
		self.name1 = self.name1 or f"doctype-{frappe.generate_hash(length=10)}"
		self.label = self.label or self.dt
		self.icon = self.icon or DEFAULT_DOCTYPE_ICON

	def validate_has_list(self):
		doctype = frappe.db.get_value("DocType", self.dt, ["istable", "issingle", "is_virtual"], as_dict=True)
		if not doctype:
			frappe.throw(_("Row {0}: DocType {1} not found.").format(self.idx, self.dt))
		if doctype.istable or doctype.issingle or doctype.is_virtual:
			frappe.throw(
				_("Row {0}: {1} is a single, child table or virtual DocType, so it has no list.").format(
					self.idx, self.dt
				)
			)


def validate_sidebar_items(settings: Document):
	"""Check the sidebar items of FCRM Settings before they are saved."""
	if not settings.meta.has_field("sidebar_items"):
		return  # code deployed, migrate not run yet

	standard_items = {item["name1"]: item for item in frappe.get_hooks("standard_sidebar_items")}
	old_settings = settings.get_doc_before_save()
	old_items = {item.name: item for item in (old_settings and old_settings.get("sidebar_items")) or []}

	keep_standard_items(settings, standard_items, old_items)
	for index, item in enumerate(settings.sidebar_items, 1):
		item.idx = index
		if item.is_standard:
			validate_standard_item(item, standard_items, old_items)
		else:
			old_item = old_items.get(item.name)
			item.validate_doctype(is_new=not old_item or old_item.dt != item.dt)
	validate_unique(settings)


def keep_standard_items(settings: Document, standard_items: dict, old_items: dict):
	"""Built-in pages can be hidden, not deleted."""
	old_keys = {item.name1 for item in old_items.values() if item.is_standard}
	new_keys = {item.name1 for item in settings.sidebar_items if item.is_standard}
	deleted = (old_keys - new_keys) & set(standard_items)
	if deleted:
		frappe.throw(_("Built-in sidebar items can't be deleted: {0}").format(", ".join(sorted(deleted))))


def validate_standard_item(item: "CRMSidebarItem", standard_items: dict, old_items: dict):
	if item.name1 in standard_items:
		item.set_standard(standard_items[item.name1])
	elif item.name not in old_items:
		frappe.throw(_("Row {0}: {1} is not a built-in page.").format(item.idx, item.name1))
	# A saved built-in the hook dropped stays until the next migrate removes it.


def validate_unique(settings: Document):
	for field, message in (
		("dt", _("{0} is in the sidebar more than once.")),
		("name1", _("Sidebar item key {0} is used more than once.")),
	):
		values = [item.get(field) for item in settings.sidebar_items if item.get(field)]
		duplicates = {value for value in values if values.count(value) > 1}
		if duplicates:
			frappe.throw(message.format(", ".join(sorted(duplicates))))


def sync_standard_sidebar_items(settings: Document):
	"""Seed the sidebar from the `standard_sidebar_items` hook and add new built-in pages at the end.
	Drop built-in pages the hook no longer lists, and DocTypes that were deleted, such as with an
	uninstalled app: their dead link would fail every save. The caller saves."""
	standard_items = frappe.get_hooks("standard_sidebar_items")
	standard_keys = {item["name1"] for item in standard_items}

	items = [item for item in settings.sidebar_items if is_still_available(item, standard_keys)]
	existing_keys = {item.name1 for item in items}
	for index, item in enumerate(items, 1):
		item.idx = index
	settings.set("sidebar_items", items)
	for item in standard_items:
		if item["name1"] not in existing_keys:
			settings.append("sidebar_items", {**item, "is_standard": 1})


def get_sidebar_items() -> list[dict]:
	"""The sidebar items the session user sees, in order. Runs in the CRM boot."""
	items = frappe.get_cached_doc("FCRM Settings").get("sidebar_items") or []
	# Building a user's permissions is not free, so only sidebars with DocTypes pay for it.
	has_doctypes = any(item.type == "DocType" for item in items)
	readable_doctypes = set(frappe.get_user().get_can_read()) if has_doctypes else set()
	return [
		{field: item.get(field) for field in BOOT_FIELDS}
		for item in items
		if not item.hidden and (item.type == "Page" or item.dt in readable_doctypes)
	]


def is_still_available(item: "CRMSidebarItem", standard_keys: set[str]) -> bool:
	if item.is_standard:
		return item.name1 in standard_keys
	return bool(frappe.db.exists("DocType", item.dt))
