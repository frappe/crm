import frappe

from crm.api.doc import get_assigned_users, get_fields_meta
from crm.fcrm.doctype.crm_form_script.crm_form_script import get_form_script


@frappe.whitelist()
def get_deal(name):
	deal = frappe.get_doc("CRM Deal", name)
	deal.check_permission("read")

	deal = deal.as_dict()

	deal["fields_meta"] = get_fields_meta("CRM Deal")
	deal["_form_script"] = get_form_script("CRM Deal")
	return deal


@frappe.whitelist()
def get_deal_contacts(name):
	contacts = frappe.get_all(
		"CRM Contacts",
		filters={"parenttype": "CRM Deal", "parent": name},
		fields=["contact", "is_primary"],
		distinct=True,
	)
	deal_contacts = []
	for contact in contacts:
		if not contact.contact:
			continue

		is_primary = contact.is_primary
		contact = frappe.get_doc("Contact", contact.contact).as_dict()

		def get_primary_email(contact):
			for email in contact.email_ids:
				if email.is_primary:
					return email.email_id
			return contact.email_ids[0].email_id if contact.email_ids else ""

		def get_primary_mobile_no(contact):
			for phone in contact.phone_nos:
				if phone.is_primary:
					return phone.phone
			return contact.phone_nos[0].phone if contact.phone_nos else ""

		_contact = {
			"name": contact.name,
			"image": contact.image,
			"full_name": contact.full_name,
			"email": get_primary_email(contact),
			"mobile_no": get_primary_mobile_no(contact),
			"is_primary": is_primary,
		}
		deal_contacts.append(_contact)
	return deal_contacts
