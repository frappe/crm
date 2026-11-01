"""The status and owner a new CRM Lead or CRM Deal starts with when the caller sends none."""

import frappe


def set_status_and_owner(doc, status_doctype: str, owner_field: str):
	if not doc.status:
		doc.status = first_status(status_doctype)
	if not doc.get(owner_field) and frappe.session.user != "Guest":
		doc.set(owner_field, frappe.session.user)
		# after_insert assigns no ToDo for this owner, so an Assignment Rule still assigns the record
		doc.flags.owner_defaulted = True


def first_status(status_doctype: str) -> str | None:
	"""The first status by `position`, as the status control lists them."""
	statuses = frappe.get_all(status_doctype, pluck="name", order_by="position asc", limit=1)
	return statuses[0] if statuses else None
