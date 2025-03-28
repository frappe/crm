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
    opportunity_names = get_linked_docs(contact, "Opportunity")

    # get opportunities data
    opportunities = []
    for opportunity_name in opportunity_names:
        opportunity = frappe.get_cached_doc(
            "Opportunity",
            opportunity_name,
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
def get_linked_docs(contact, link_doctype):
    contact_doc = frappe.get_doc("Contact", contact)

    names = []
    for link in contact_doc.links:
        if link.link_doctype == link_doctype:
            names.append(link.link_name)

    return names


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
    link_names = [link_name]
    link_doctypes = [link_doctype]
    if link_doctype == "Opportunity":
        opportunity = frappe.get_cached_doc("Opportunity", link_name)
        if opportunity.opportunity_from:
            link_doctypes.append(opportunity.opportunity_from)
            link_names.append(opportunity.party_name)

    contacts = frappe.get_list(
        "Contact",
        [
            ["Dynamic Link", "link_doctype", "in", link_doctypes],
            ["Dynamic Link", "link_name", "in", link_names],
        ],
        distinct=True,
        pluck="name",
    )

    return contacts


@frappe.whitelist()
def link_contact_to_doc(contact, doctype, docname):
    if not frappe.has_permission(doctype, "write", docname):
        frappe.throw(_("Not allowed to link contact to doc"), frappe.PermissionError)

    contact_doc = frappe.get_doc("Contact", contact)

    if doctype == "Opportunity":
        opportunity_doc = frappe.get_cached_doc("Opportunity", docname)

        if opportunity_doc.opportunity_from:
            contact_doc.append(
                "links",
                {
                    "link_doctype": opportunity_doc.opportunity_from,
                    "link_name": opportunity_doc.party_name,
                },
            )

    contact_doc.append("links", {"link_doctype": doctype, "link_name": docname})
    contact_doc.save()

    return contact_doc.name


@frappe.whitelist()
def remove_link_from_contact(contact, doctype, docname):
    if not frappe.has_permission(doctype, "write", docname):
        frappe.throw(_("Not allowed to remove contact"), frappe.PermissionError)

    contact_doc = frappe.get_doc("Contact", contact)

    link_names = [docname]
    if doctype == "Opportunity":
        opportunity_doc = frappe.get_cached_doc("Opportunity", docname)
        if opportunity_doc.opportunity_from:
            link_names.append(opportunity_doc.party_name)

    contact_doc.links = [d for d in contact_doc.links if d.link_name not in link_names]
    contact_doc.save()

    return contact_doc.name


@frappe.whitelist()
def get_lead_opportunity_contacts(doctype, docname):
    contacts = get_linked_contact(doctype, docname)
    linked_contacts = []
    for contact in contacts:
        contact = frappe.get_doc("Contact", contact).as_dict()

        _contact = {
            "name": contact.name,
            "image": contact.image,
            "full_name": contact.full_name,
            "email": get_primary_email(contact),
            "mobile_no": get_primary_mobile_no(contact),
            "is_primary_contact": contact.is_primary_contact,
        }
        linked_contacts.append(_contact)
    return linked_contacts


@frappe.whitelist()
def set_primary_contact(doctype, docname, contact=None):
    linked_contacts = get_linked_contact(doctype, docname)
    if not linked_contacts:
        return

    if not contact and len(linked_contacts) == 1:
        contact_doc = frappe.get_doc("Contact", linked_contacts[0])
        contact_doc.is_primary_contact = 1
        contact_doc.save()
    elif contact:
        for linked_contact in linked_contacts:
            primary = 0
            if contact == linked_contact:
                primary = 1
            frappe.db.set_value(
                "Contact", linked_contact, "is_primary_contact", primary
            )
    return True


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
