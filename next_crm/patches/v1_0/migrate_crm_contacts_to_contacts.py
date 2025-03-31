import frappe


def execute():
    batch_size = 100
    start = 0

    while True:
        crm_contacts = frappe.get_list(
            "CRM Contacts",
            fields="name",
            pluck="name",
            start=start,
            page_length=batch_size,
        )

        if not crm_contacts:
            break

        for crm_contact in crm_contacts:
            crm_contact_doc = frappe.get_doc("CRM Contacts", crm_contact)
            link = frappe.new_doc("Dynamic Link")
            link.parenttype = "Contact"
            link.parentfield = "links"
            link.parent = crm_contact_doc.contact
            link.link_name = crm_contact_doc.parent
            link.link_doctype = crm_contact_doc.parenttype
            link.owner = crm_contact_doc.owner
            if (
                crm_contact_doc.is_primary
                and crm_contact_doc.parenttype == "Opportunity"
            ):
                opportunity_doc = frappe.get_doc("Opportunity", crm_contact_doc.parent)
                opportunity_doc.contact_person = crm_contact_doc.contact
                opportunity_doc.save()
            link.save()

        frappe.db.commit()

        start += batch_size
