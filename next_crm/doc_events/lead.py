import frappe


def on_trash(doc, method=None):
    frappe.db.delete(
        "Dynamic Link",
        filters={"link_name": doc.name, "parenttype": ["in", ["Contact", "Address"]]},
    )
    frappe.db.delete(
        "Event",
        filters=[
            ["Event Participants", "reference_doctype", "=", "Lead"],
            ["Event Participants", "reference_docname", "=", doc.name],
        ],
    )
    frappe.db.delete(
        "Event Participants",
        filters=[
            ["reference_doctype", "=", "Lead"],
            ["reference_docname", "=", doc.name],
        ],
    )
    frappe.db.delete("CRM Notification", {"reference_name": doc.name})
    gmail_threads = frappe.get_list(
        "Gmail Thread",
        filters={
            "reference_doctype": "Lead",
            "reference_name": doc.name,
        },
        pluck="name",
    )
    for thread in gmail_threads:
        frappe.db.set_value(
            "Gmail Thread",
            thread,
            {"reference_doctype": None, "reference_name": None, "status": "Open"},
        )
