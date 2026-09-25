import frappe
from frappe import _


@frappe.whitelist()
def get_deal_contacts(name: str):
	if not frappe.has_permission("CRM Deal", "read", name):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	contacts = frappe.get_all(
		"CRM Contacts",
		filters={"parenttype": "CRM Deal", "parent": name},
		fields=["contact", "is_primary"],
		order_by="is_primary desc, idx asc",
		distinct=True,
	)
	deal_contacts = []
	for contact in contacts:
		if not contact.contact:
			continue

		is_primary = contact.is_primary
		contact = frappe.get_doc("Contact", contact.contact).as_dict()

		_contact = {
			"name": contact.name,
			"image": contact.image,
			"full_name": contact.full_name,
			"email": contact.email_id,
			"mobile_no": contact.mobile_no,
			"is_primary": is_primary,
		}
		deal_contacts.append(_contact)
	return deal_contacts

@frappe.whitelist()
def get_deal_quotations(name: str):
	"""Fetch ERPNext Quotations linked to a CRM Deal."""
	if not name or not isinstance(name, str):
		return []

	# Check permission on CRM Deal
	if not frappe.has_permission("CRM Deal", ptype="read", doc=name):
		frappe.throw(_("Not permitted to view quotations for this Deal"), frappe.PermissionError)

	# Check if Quotation DocType exists (e.g. ERPNext installed)
	if not frappe.db.exists("DocType", "Quotation"):
		return []

	# Check permission on Quotation
	if not frappe.has_permission("Quotation", ptype="read"):
		return []

	return frappe.get_all(
		"Quotation",
		filters={"crm_deal": name},
		fields=[
			"name",
			"status",
			"transaction_date",
			"valid_till",
			"grand_total",
			"currency",
			"docstatus",
			"customer_name",
		],
		order_by="creation desc",
	)
