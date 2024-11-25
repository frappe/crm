import json

import frappe


def execute():
    if not frappe.db.exists("CRM Fields Layout", "Opportunity-Quick Entry"):
        return

    opportunity = frappe.db.get_value(
        "CRM Fields Layout", "Opportunity-Quick Entry", "layout"
    )

    layout = json.loads(opportunity)
    for section in layout:
        if section.get("label") in [
            "Select Customer",
            "Customer Details",
            "Select Contact",
        ]:
            section["editable"] = False

    frappe.db.set_value(
        "CRM Fields Layout", "Opportunity-Quick Entry", "layout", json.dumps(layout)
    )
