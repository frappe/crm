import frappe

from next_crm.api.whatsapp import get_lead_or_opportunity_from_number, notify_agent


def validate(doc, method=None):
    if doc.type == "Incoming" and doc.get("from"):
        name, doctype = get_lead_or_opportunity_from_number(doc.get("from"))
        doc.reference_doctype = doctype
        doc.reference_name = name


def on_update(doc, method=None):
    frappe.publish_realtime(
        "whatsapp_message",
        {
            "reference_doctype": doc.reference_doctype,
            "reference_name": doc.reference_name,
        },
    )

    notify_agent(doc)
