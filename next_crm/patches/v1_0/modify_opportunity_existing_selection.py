import json

import frappe


def execute():
    if not frappe.db.exists("CRM Fields Layout", "Opportunity-Quick Entry"):
        return

    quickentry = frappe.get_doc("CRM Fields Layout", "Opportunity-Quick Entry")
    parsed_layout = json.loads(quickentry.layout)
    for section in parsed_layout:
        if section.get("label") == "Select Customer":
            section["label"] = "Select Opportunity From"
            section["fields"] = ["opportunity_from", "party_name"]
            section["columns"] = 2

    quickentry.layout = json.dumps(parsed_layout)
    quickentry.save()
