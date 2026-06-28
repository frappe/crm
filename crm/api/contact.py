import frappe
from frappe import _


def validate(doc, method):
	update_deals_email_mobile_no(doc)


def update_deals_email_mobile_no(doc):
	linked_deals = frappe.get_all(
		"CRM Contacts",
		filters={"contact": doc.name, "is_primary": 1},
		fields=["parenttype", "parent"],
	)

	for linked_deal in linked_deals:
		deal = frappe.db.get_values(linked_deal.parenttype, linked_deal.parent, ["email", "mobile_no"], as_dict=True)[0]
		if deal.email != doc.email_id or deal.mobile_no != doc.mobile_no:
			frappe.db.set_value(
				linked_deal.parenttype,
				linked_deal.parent,
				{
					"email": doc.email_id,
					"mobile_no": doc.mobile_no,
				},
			)


@frappe.whitelist()
def get_linked_deals(contact: str):
	"""Get linked deals for a contact"""

	if not frappe.has_permission("Contact", "read", contact):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

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
def create_new(contact: str, field: str, value: str):
	"""Create new email or phone for a contact"""
	if not frappe.has_permission("Contact", "write", contact):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	contact = frappe.get_cached_doc("Contact", contact)

	if field == "email":
		email = {"email_id": value, "is_primary": 1 if len(contact.email_ids) == 0 else 0}
		contact.append("email_ids", email)
	elif field in ("mobile_no", "phone"):
		mobile_no = {"phone": value, "is_primary_mobile_no": 1 if len(contact.phone_nos) == 0 else 0}
		contact.append("phone_nos", mobile_no)
	else:
		frappe.throw(_("Invalid field"))

	contact.save()
	return True


@frappe.whitelist()
def set_as_primary(contact: str, field: str, value: str):
	"""Set email or phone as primary for a contact"""
	if not frappe.has_permission("Contact", "write", contact):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

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
		frappe.throw(_("Invalid field"))

	contact.save()
	return True


@frappe.whitelist()
def get_linked_lead(contact: str):
    """Get a lead linked to a contact by matching email or mobile number"""
    if not frappe.has_permission("Contact", "read", contact):
        frappe.throw(_("Not permitted"), frappe.PermissionError)

    contact_doc = frappe.get_cached_doc("Contact", contact)
    email = contact_doc.email_id
    mobile_no = contact_doc.mobile_no
    if not email and not mobile_no:
        return None

    lead = frappe.get_all(
		"CRM Lead",
		or_filters=[
            ["email", "=", email],
            ["mobile_no", "=", mobile_no],
        ],
		fields=["name"],
		pluck='name',
		limit=1,
	)
    return lead[0] if lead else None


@frappe.whitelist()
def create_lead_from_contact(contact: str):
    """Create a new CRM Lead from contact data"""
    if not frappe.has_permission("Contact", "read", contact):
        frappe.throw(_("Not permitted"), frappe.PermissionError)
    if not frappe.has_permission("CRM Lead", "create"):
        frappe.throw(_("Not permitted to create Lead"), frappe.PermissionError)

    contact_doc = frappe.get_cached_doc("Contact", contact)
    if not contact_doc.email_id and not contact_doc.mobile_no:
        frappe.throw(_("Contact must have either an email or mobile number to create a Lead"))

    lead = frappe.new_doc("CRM Lead")
    lead.first_name = contact_doc.first_name or contact_doc.full_name
    lead.last_name = contact_doc.last_name
    lead.salutation = contact_doc.salutation
    lead.email = contact_doc.email_id
    lead.mobile_no = contact_doc.mobile_no
    lead.image = contact_doc.image
    lead.organization = contact_doc.company_name
    lead.insert()

    return lead.name


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
