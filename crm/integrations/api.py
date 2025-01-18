import frappe
from frappe.query_builder import Order
from pypika.functions import Replace

from crm.utils import are_same_phone_number, parse_phone_number


@frappe.whitelist()
def is_call_integration_enabled():
	twilio_enabled = frappe.db.get_single_value("Twilio Settings", "enabled")
	exotel_enabled = frappe.db.get_single_value("CRM Exotel Settings", "enabled")
	default_calling_medium = frappe.db.get_single_value("FCRM Settings", "default_calling_medium")

	return {
		"twilio_enabled": twilio_enabled,
		"exotel_enabled": exotel_enabled,
		"default_calling_medium": default_calling_medium,
	}


@frappe.whitelist()
def set_default_calling_medium(medium):
	return frappe.db.set_value("FCRM Settings", "FCRM Settings", "default_calling_medium", medium)


@frappe.whitelist()
def create_and_add_note_to_call_log(call_sid, content):
	"""Add note to call log based on call sid."""
	note = frappe.get_doc(
		{
			"doctype": "FCRM Note",
			"content": content,
		}
	).insert(ignore_permissions=True)

	call_log = frappe.get_doc("CRM Call Log", call_sid)
	call_log.link_with_reference_doc("FCRM Note", note.name)
	call_log.save(ignore_permissions=True)


@frappe.whitelist()
def create_and_add_task_to_call_log(call_sid, task):
	"""Add task to call log based on call sid."""
	_task = frappe.get_doc(
		{
			"doctype": "CRM Task",
			"title": task.get("title"),
			"description": task.get("description"),
		}
	).insert(ignore_permissions=True)

	call_log = frappe.get_doc("CRM Call Log", call_sid)
	call_log.link_with_reference_doc("CRM Task", _task.name)
	call_log.save(ignore_permissions=True)


@frappe.whitelist()
def get_contact_by_phone_number(phone_number):
	"""Get contact by phone number."""
	number = parse_phone_number(phone_number)

	if number.get("is_valid"):
		return get_contact(number.get("national_number"))
	else:
		return get_contact(phone_number, exact_match=True)


def get_contact(phone_number, exact_match=False):
	cleaned_number = (
		phone_number.strip()
		.replace(" ", "")
		.replace("-", "")
		.replace("(", "")
		.replace(")", "")
		.replace("+", "")
	)

	# Check if the number is associated with a contact
	Contact = frappe.qb.DocType("Contact")
	normalized_phone = Replace(
		Replace(Replace(Replace(Replace(Contact.mobile_no, " ", ""), "-", ""), "(", ""), ")", ""), "+", ""
	)

	query = (
		frappe.qb.from_(Contact)
		.select(Contact.name, Contact.full_name, Contact.image, Contact.mobile_no)
		.where(normalized_phone.like(f"%{cleaned_number}%"))
		.orderby("modified", order=Order.desc)
	)
	contacts = query.run(as_dict=True)

	if len(contacts):
		# Check if the contact is associated with a deal
		for contact in contacts:
			if frappe.db.exists("CRM Contacts", {"contact": contact.name, "is_primary": 1}):
				deal = frappe.db.get_value(
					"CRM Contacts", {"contact": contact.name, "is_primary": 1}, "parent"
				)
				if are_same_phone_number(contact.mobile_no, phone_number, validate=not exact_match):
					contact["deal"] = deal
					return contact
		# Else, return the first contact
		if are_same_phone_number(contacts[0].mobile_no, phone_number, validate=not exact_match):
			return contacts[0]

	# Else, Check if the number is associated with a lead
	Lead = frappe.qb.DocType("CRM Lead")
	normalized_phone = Replace(
		Replace(Replace(Replace(Replace(Lead.mobile_no, " ", ""), "-", ""), "(", ""), ")", ""), "+", ""
	)

	query = (
		frappe.qb.from_(Lead)
		.select(Lead.name, Lead.lead_name, Lead.image, Lead.mobile_no)
		.where(Lead.converted == 0)
		.where(normalized_phone.like(f"%{cleaned_number}%"))
		.orderby("modified", order=Order.desc)
	)
	leads = query.run(as_dict=True)

	if len(leads):
		for lead in leads:
			if are_same_phone_number(lead.mobile_no, phone_number, validate=not exact_match):
				lead["lead"] = lead.name
				return lead

	return {"mobile_no": phone_number}
