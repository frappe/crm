from typing import Literal

import frappe
from frappe import _

from crm.api import check_app_permission
from crm.fcrm.doctype.crm_sidebar.sidebar import Sidebar


@frappe.whitelist(methods=["GET"])
def get_sidebar() -> list[dict]:
	"""Return the CRM sidebar the current user sees, in the order it draws.

	It is the standard items, then the site's changes, then the user's own. Hidden items and
	DocTypes the user cannot read are left out. Each item has a key, a type (Link or Section),
	a label, an icon, a link_type (Built-in or DocType), a link_to and the parent_key of the
	section it sits in.
	"""
	check_crm_user()
	return Sidebar().get_items()


@frappe.whitelist(methods=["GET"])
def get_sidebar_layer(scope: Literal["user", "site"] = "user") -> dict:
	"""Return one layer of the sidebar for editing.

	scope: "user" for the current user's own changes, or "site" for everyone's (System
	Manager and Sales Manager only).
	Returns the items as this layer shows them, the items of the layer below, and the layer's
	`modified`, which save_sidebar_layer needs.
	"""
	check_crm_user()
	return Sidebar().get_layer(scope)


@frappe.whitelist(methods=["POST"])
def save_sidebar_layer(
	scope: Literal["user", "site"], items: list[dict], modified: str | None = None
) -> dict:
	"""Save the whole ordered sidebar a layer should show; the server stores only the changes.

	scope: "user" or "site", as in get_sidebar_layer.
	items: every item in order, as get_sidebar_layer returned them, after the edits. Items a
	layer adds have the key "<scope>:" followed by 4 to 16 lowercase letters or digits.
	modified: the layer's `modified` from get_sidebar_layer. The save fails if the layer
	changed since.
	Sending the items of the layer below removes the layer.
	"""
	check_crm_user()
	return Sidebar().save_layer(scope, items, modified)


@frappe.whitelist(methods=["GET"])
def search_sidebar_doctypes(txt: str = "") -> list[str]:
	"""Return up to 20 DocTypes the current user can read that have a list to open.

	Single, child table and virtual DocTypes are left out. txt: part of the DocType's name.
	"""
	check_crm_user()
	return Sidebar().search_doctypes(txt)


def get_sidebar_for_boot() -> list[dict] | None:
	"""The sidebar for the page boot; None before the migrate that adds CRM Sidebar."""
	try:
		return Sidebar().get_items()
	except Exception as e:
		if frappe.db.is_table_missing(e):
			return None
		raise


def check_crm_user():
	if not check_app_permission():
		frappe.throw(_("You do not have permission to access Frappe CRM"), frappe.PermissionError)
