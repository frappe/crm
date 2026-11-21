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
			# Every email and phone, so the deal side panel can edit them in place
			"email_ids": [{"name": e.name, "email_id": e.email_id} for e in contact.email_ids],
			"phone_nos": [{"name": p.name, "phone": p.phone} for p in contact.phone_nos],
			"can_write": frappe.has_permission("Contact", "write", contact.name),
		}
		deal_contacts.append(_contact)
	return deal_contacts
