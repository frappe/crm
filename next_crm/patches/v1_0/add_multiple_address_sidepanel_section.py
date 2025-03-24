import json

import frappe


def execute():
    if not frappe.db.exists(
        "CRM Fields Layout", "Lead-Side Panel"
    ) or not frappe.db.exists("CRM Fields Layout", "Opportunity-Side Panel"):
        return

    address_section = {
        "label": "Addresses",
        "name": "addresses_section",
        "opened": True,
        "editable": False,
        "addresses": [],
    }
    doctypes = ["Lead", "Opportunity"]

    for doctype in doctypes:
        docpanel = frappe.get_doc("CRM Fields Layout", f"{doctype}-Side Panel")
        parsed_layout = json.loads(docpanel.layout)
        if not any(item.get("name") == "addresses_section" for item in parsed_layout):
            parsed_layout.insert(0, address_section)
        docpanel.layout = json.dumps(parsed_layout)
        docpanel.save()
