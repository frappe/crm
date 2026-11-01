"""The status and owner a new CRM Lead or CRM Deal starts with when the caller sends none."""

import frappe


def set_status_and_owner(doc, status_doctype: str, owner_field: str):
	if not doc.status:
		doc.status = first_status(status_doctype)
	if not doc.get(owner_field) and created_by_a_user():
		doc.set(owner_field, frappe.session.user)
		# after_insert assigns no ToDo for this owner, so an Assignment Rule still assigns the record
		doc.flags.owner_defaulted = True


def created_by_a_user() -> bool:
	"""False for a guest, a background job (lead sync, email to lead), a data import or a web form."""
	if frappe.session.user == "Guest" or getattr(frappe.local, "job", None):
		return False
	return not (frappe.flags.in_import or frappe.flags.in_web_form)


def first_status(status_doctype: str) -> str | None:
	"""The first status by `position`, as the status control lists them."""
	statuses = frappe.get_all(status_doctype, pluck="name", order_by="position asc, creation asc", limit=1)
	return statuses[0] if statuses else None
