import frappe
from frappe import _

from next_crm.api.doc import get_assigned_users, get_fields_meta
from next_crm.ncrm.doctype.crm_form_script.crm_form_script import get_form_script


@frappe.whitelist()
def get_opportunity(name):
    Opportunity = frappe.qb.DocType("Opportunity")

    query = (
        frappe.qb.from_(Opportunity)
        .select("*")
        .where(Opportunity.name == name)
        .limit(1)
    )

    opportunity = query.run(as_dict=True)
    if not len(opportunity):
        frappe.throw(_("Opportunity not found"), frappe.DoesNotExistError)
    opportunity = opportunity.pop()

    opportunity["contacts"] = frappe.get_all(
        "CRM Contacts",
        filters={"parenttype": "Opportunity", "parent": opportunity.name},
        fields=["contact", "is_primary"],
    )

    opportunity["doctype"] = "Opportunity"
    opportunity["fields_meta"] = get_fields_meta("Opportunity")
    opportunity["_form_script"] = get_form_script("Opportunity")
    opportunity["_assign"] = get_assigned_users("Opportunity", opportunity.name)
    return opportunity


@frappe.whitelist()
def get_opportunity_contacts(name):
    contacts = frappe.get_all(
        "CRM Contacts",
        filters={"parenttype": "Opportunity", "parent": name},
        fields=["contact", "is_primary"],
    )
    opportunity_contacts = []
    for contact in contacts:
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
        opportunity_contacts.append(_contact)
    return opportunity_contacts
