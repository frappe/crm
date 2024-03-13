import frappe
from frappe import _


def validate(doc, method):
	set_primary_email(doc)
	set_primary_mobile_no(doc)
	doc.set_primary_email()
	doc.set_primary("mobile_no")


def set_primary_email(doc):
	if not doc.email_ids:
		return

	if len(doc.email_ids) == 1:
		doc.email_ids[0].is_primary = 1


def set_primary_mobile_no(doc):
	if not doc.phone_nos:
		return

	if len(doc.phone_nos) == 1:
		doc.phone_nos[0].is_primary_mobile_no = 1


@frappe.whitelist()
def get_contact(name):
	Contact = frappe.qb.DocType("Contact")

	query = (
		frappe.qb.from_(Contact)
		.select("*")
		.where(Contact.name == name)
		.limit(1)
	)

	contact = query.run(as_dict=True)
	if not len(contact):
		frappe.throw(_("Contact not found"), frappe.DoesNotExistError)
	contact = contact.pop()

	contact["doctype"] = "Contact"
	contact["email_ids"] = frappe.get_all(
		"Contact Email", filters={"parent": name}, fields=["name", "email_id", "is_primary"]
	)
	contact["phone_nos"] = frappe.get_all(
		"Contact Phone", filters={"parent": name}, fields=["name", "phone", "is_primary_mobile_no"]
	)
	return contact

@frappe.whitelist()
def get_linked_deals(contact):
	"""Get linked deals for a contact"""

	if not frappe.has_permission("Contact", "read", contact):
		frappe.throw("Not permitted", frappe.PermissionError)

	deal_names = frappe.get_all(
		"CRM Contacts",
		filters={"contact": contact, "parenttype": "CRM Deal"},
		fields=["parent"],
		distinct=True,
	)

	# get deals data
	deals = []
	for d in deal_names:
		deal = frappe.get_cached_doc(
			"CRM Deal",
			d.parent,
			fields=[
				"name",
				"organization",
				"annual_revenue",
				"status",
				"email",
				"mobile_no",
				"deal_owner",
				"modified",
			],
		)
		deals.append(deal.as_dict())

	return deals


@frappe.whitelist()
def create_new(contact, field, value):
	"""Create new email or phone for a contact"""
	if not frappe.has_permission("Contact", "write", contact):
		frappe.throw("Not permitted", frappe.PermissionError)

	contact = frappe.get_doc("Contact", contact)

	if field == "email":
		contact.append("email_ids", {"email_id": value})
	elif field in ("mobile_no", "phone"):
		contact.append("phone_nos", {"phone": value})
	else:
		frappe.throw("Invalid field")

	contact.save()
	return True


@frappe.whitelist()
def set_as_primary(contact, field, value):
	"""Set email or phone as primary for a contact"""
	if not frappe.has_permission("Contact", "write", contact):
		frappe.throw("Not permitted", frappe.PermissionError)

	contact = frappe.get_doc("Contact", contact)

	if field == "email":
		for email in contact.email_ids:
			if email.email_id == value:
				email.is_primary = 1
			else:
				email.is_primary = 0
	elif field in ("mobile_no", "phone"):
		name = "is_primary_mobile_no" if field == "mobile_no" else "is_primary_phone"
		for phone in contact.phone_nos:
			if phone.phone == value:
				phone.set(name, 1)
			else:
				phone.set(name, 0)
	else:
		frappe.throw("Invalid field")

	contact.save()
	return True
