import json

import frappe


def execute():
    if not frappe.db.exists("CRM Fields Layout", "Lead-Side Panel"):
        return

    contact_section = {
        "label": "Contacts",
        "name": "contacts_section",
        "opened": True,
        "editable": False,
        "contacts": [],
    }

    docpanel = frappe.get_doc("CRM Fields Layout", "Lead-Side Panel")
    parsed_layout = json.loads(docpanel.layout)
    if not any(item.get("name") == "contacts_section" for item in parsed_layout):
        if parsed_layout[0].get("name") == "addresses_section":
            parsed_layout.insert(1, contact_section)
        else:
            parsed_layout.insert(0, contact_section)
    docpanel.layout = json.dumps(parsed_layout)
    docpanel.save()
