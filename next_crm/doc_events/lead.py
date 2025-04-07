import frappe


def on_trash(doc, method=None):
    frappe.db.delete("Prospect Lead", filters={"lead": doc.name})
    frappe.db.delete(
        "Dynamic Link",
        filters={"link_name": doc.name, "parenttype": ["in", ["Contact", "Address"]]},
    )
    delete_linked_event(doc.name)
    frappe.db.delete("CRM Notification", {"reference_name": doc.name})
    unlink_gmail_thread(doc.name)


def delete_linked_event(docname):
    event_part = frappe.qb.DocType("Event Participants")
    event_participants_query = (
        frappe.qb.from_(event_part)
        .where(event_part.reference_doctype == "Lead")
        .where(event_part.reference_docname == docname)
        .select(event_part.parent)
    )

    event = frappe.qb.DocType("Event")
    event_delete_query = (
        frappe.qb.from_(event)
        .where(event.name.isin(event_participants_query))
        .delete()
        .get_sql()
    )

    event_participants_delete_query = (
        frappe.qb.from_(event_part)
        .where(event_part.parent.isin(event_participants_query))
        .delete()
        .get_sql()
    )

    frappe.db.sql(event_delete_query)
    frappe.db.sql(event_participants_delete_query)


def unlink_gmail_thread(docname):
    gmail_thread = frappe.qb.DocType("Gmail Thread")

    query = (
        frappe.qb.update(gmail_thread)
        .set(gmail_thread.reference_doctype, None)
        .set(gmail_thread.reference_name, None)
        .set(gmail_thread.status, "Open")
        .where(gmail_thread.reference_doctype == "Lead")
        .where(gmail_thread.reference_name == docname)
        .get_sql()
    )

    frappe.db.sql(query)
