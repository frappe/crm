import frappe
from frappe import _
from frappe.model.rename_doc import rename_doc

CASCADE_FLAG = "crm_product_item_cascade_in_progress"
ALLOWED_DOCTYPES = ("CRM Product", "Item")


def should_sync() -> bool:
	"""Product sync runs only when integration is enabled AND same-site."""
	if "erpnext" not in frappe.get_installed_apps():
		return False
	settings = frappe.get_cached_doc("ERPNext CRM Settings")
	return bool(settings.enabled) and not settings.is_erpnext_in_different_site


def in_cascade() -> bool:
	return bool(frappe.flags.get(CASCADE_FLAG))


def set_links(item_code: str, crm_product_name: str) -> None:
	"""Permission-bypassing link bookkeeping. Mirrors HD's set_links."""
	frappe.db.set_value(
		"CRM Product", crm_product_name, "erpnext_item_code", item_code, update_modified=False
	)
	frappe.db.set_value(
		"Item", item_code, "crm_product_code", crm_product_name, update_modified=False
	)


def _other_side(self_doctype: str) -> tuple[str, str]:
	if self_doctype == "CRM Product":
		return "Item", "crm_product_code"
	return "CRM Product", "erpnext_item_code"


def find_target_for(doctype: str | None, value: str | None) -> tuple[str, str] | None:
	if not doctype or not value:
		return None
	if doctype == "CRM Product":
		item = frappe.db.get_value("Item", {"crm_product_code": value}, "name")
		return ("Item", item) if item else None
	if doctype == "Item":
		prod = frappe.db.get_value("CRM Product", {"erpnext_item_code": value}, "name")
		return ("CRM Product", prod) if prod else None
	return None


def validate_rename_conflict(self_doctype, olddn, newdn, merge):
	if in_cascade() or not should_sync():
		return
	other_doctype, other_link_field = _other_side(self_doctype)
	linked = frappe.db.get_value(other_doctype, {other_link_field: olddn}, "name")
	if not linked:
		return
	if merge:
		surviving = frappe.db.get_value(other_doctype, {other_link_field: newdn}, "name")
		if surviving:
			return
	if linked == newdn:
		return
	if frappe.db.exists(other_doctype, newdn):
		existing_link = frappe.db.get_value(other_doctype, newdn, other_link_field)
		if existing_link != olddn:
			frappe.throw(
				_(
					"Cannot rename: an unrelated {0} '{1}' already exists on the "
					"other side. Resolve manually first."
				).format(other_doctype, newdn)
			)


def cascade_rename(self_doctype, olddn, newdn, merge):
	if in_cascade() or not should_sync():
		return
	other_doctype, other_link_field = _other_side(self_doctype)
	linked = frappe.db.get_value(other_doctype, {other_link_field: olddn}, "name")
	if not linked:
		return
	frappe.flags[CASCADE_FLAG] = True
	try:
		if merge:
			surviving = frappe.db.get_value(other_doctype, {other_link_field: newdn}, "name")
			if surviving and surviving != linked:
				rename_doc(other_doctype, linked, surviving, merge=True, ignore_permissions=True)
				target = surviving
			else:
				if linked != newdn:
					rename_doc(other_doctype, linked, newdn, ignore_permissions=True)
				target = newdn
		else:
			if linked != newdn:
				rename_doc(other_doctype, linked, newdn, ignore_permissions=True)
			target = newdn
		_resync_links(self_doctype, newdn, target)
	finally:
		frappe.flags[CASCADE_FLAG] = False


def _resync_links(self_doctype, self_name, other_name):
	if self_doctype == "CRM Product":
		prod, item = self_name, other_name
	else:
		prod, item = other_name, self_name
	if frappe.db.exists("CRM Product", prod):
		frappe.db.set_value(
			"CRM Product", prod, "erpnext_item_code", item, update_modified=False
		)
	if frappe.db.exists("Item", item):
		frappe.db.set_value("Item", item, "crm_product_code", prod, update_modified=False)
