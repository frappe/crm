import frappe
from frappe import _


def validate(doc, method):
	update_deals_email_mobile_no(doc)


def update_deals_email_mobile_no(doc):
	linked_deals = frappe.get_all(
		"CRM Contacts",
		filters={"contact": doc.name, "is_primary": 1},
		fields=["parent"],
	)

	for linked_deal in linked_deals:
		deal = frappe.get_cached_doc("CRM Deal", linked_deal.parent)
		if deal.email != doc.email_id or deal.mobile_no != doc.mobile_no:
			deal.email = doc.email_id
			deal.mobile_no = doc.mobile_no
			deal.save(ignore_permissions=True)


@frappe.whitelist()
def get_contact(name):
	contact = frappe.get_doc("Contact", name)
	contact.check_permission("read")

	contact = contact.as_dict()

	if not len(contact):
		frappe.throw(_("Contact not found"), frappe.DoesNotExistError)

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
				"currency",
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

	contact = frappe.get_cached_doc("Contact", contact)

	if field == "email":
		email = {"email_id": value, "is_primary": 1 if len(contact.email_ids) == 0 else 0}
		contact.append("email_ids", email)
	elif field in ("mobile_no", "phone"):
		mobile_no = {"phone": value, "is_primary_mobile_no": 1 if len(contact.phone_nos) == 0 else 0}
		contact.append("phone_nos", mobile_no)
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


@frappe.whitelist()
def search_emails(txt: str):
	doctype = "Contact"
	meta = frappe.get_meta(doctype)
	filters = [["Contact", "email_id", "is", "set"]]

	if meta.get("fields", {"fieldname": "enabled", "fieldtype": "Check"}):
		filters.append([doctype, "enabled", "=", 1])
	if meta.get("fields", {"fieldname": "disabled", "fieldtype": "Check"}):
		filters.append([doctype, "disabled", "!=", 1])

	or_filters = []
	search_fields = ["full_name", "email_id", "name"]
	if txt:
		for f in search_fields:
			or_filters.append([doctype, f.strip(), "like", f"%{txt}%"])

	results = frappe.get_list(
		doctype,
		filters=filters,
		fields=search_fields,
		or_filters=or_filters,
		limit_start=0,
		limit_page_length=20,
		order_by="email_id, full_name, name",
		ignore_permissions=False,
		as_list=True,
		strict=False,
	)

	return results
