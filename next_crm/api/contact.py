import frappe
from frappe import _


def validate(doc, method):
    set_primary_email(doc)
    set_primary_mobile_no(doc)
    doc.set_primary_email()
    doc.set_primary("mobile_no")
    update_opportunities_email_mobile_no(doc)


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


def update_opportunities_email_mobile_no(doc):
    linked_opportunities = frappe.get_all(
        "CRM Contacts",
        filters={"contact": doc.name, "is_primary": 1},
        fields=["parent"],
    )

    for linked_opportunity in linked_opportunities:
        opportunity = frappe.get_cached_doc("Opportunity", linked_opportunity.parent)
        if (
            opportunity.contact_email != doc.email_id
            or opportunity.contact_mobile != doc.mobile_no
        ):
            opportunity.contact_email = doc.email_id
            opportunity.contact_mobile = doc.mobile_no
            opportunity.save(ignore_permissions=True)


@frappe.whitelist()
def get_contact(name):
    Contact = frappe.qb.DocType("Contact")

    query = frappe.qb.from_(Contact).select("*").where(Contact.name == name).limit(1)

    contact = query.run(as_dict=True)
    if not len(contact):
        frappe.throw(_("Contact not found"), frappe.DoesNotExistError)
    contact = contact.pop()

    contact["doctype"] = "Contact"
    contact["email_ids"] = frappe.get_all(
        "Contact Email",
        filters={"parent": name},
        fields=["name", "email_id", "is_primary"],
    )
    contact["phone_nos"] = frappe.get_all(
        "Contact Phone",
        filters={"parent": name},
        fields=["name", "phone", "is_primary_mobile_no"],
    )
    return contact


@frappe.whitelist()
def get_linked_opportunities(contact):
    """Get linked opportunities for a contact"""

    if not frappe.has_permission("Contact", "read", contact):
        frappe.throw("Not permitted", frappe.PermissionError)

    opportunity_names = frappe.get_all(
        "CRM Contacts",
        filters={"contact": contact, "parenttype": "Opportunity"},
        fields=["parent"],
        distinct=True,
    )

    # get opportunities data
    opportunities = []
    for d in opportunity_names:
        opportunity = frappe.get_cached_doc(
            "Opportunity",
            d.parent,
            fields=[
                "name",
                "customer",
                "currency",
                "opportunity_amount",
                "status",
                "contact_email",
                "contact_mobile",
                "opportunity_owner",
                "modified",
            ],
        )
        opportunities.append(opportunity.as_dict())

    return opportunities


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

    if field == "email_id":
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


@frappe.whitelist()
def get_linked_contact(link_doctype, link_name):
    contacts = frappe.get_list(
        "Contact",
        [
            ["Dynamic Link", "link_doctype", "=", link_doctype],
            ["Dynamic Link", "link_name", "=", link_name],
        ],
        pluck="name",
    )

    return contacts
