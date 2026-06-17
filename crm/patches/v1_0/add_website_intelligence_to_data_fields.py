"""Surface the enriched fields in the "Data" tab (Data Fields layout) for existing
installs of CRM Lead and CRM Deal.

The Data tab exists only for Lead and Deal (Organization has no Data tab). The
layout can be flat (`[{columns}]`, Lead) or tabbed (`[{sections:[{columns}]}]`,
Deal), so we walk either shape and append only the missing fieldnames to the first
real column — never removing or reordering existing fields. Idempotent.
"""

import json

import frappe

FIELDS_TO_ADD = ["company_description", "industry", "no_of_employees",
                 "linkedin", "twitter", "key_people"]
DOCTYPES = ("CRM Lead", "CRM Deal")


def execute():
    for doctype in DOCTYPES:
        _add_fields_to_data_layout(doctype)


def _add_fields_to_data_layout(doctype):
    name = frappe.db.get_value(
        "CRM Fields Layout", {"dt": doctype, "type": "Data Fields"})
    if not name:
        return  # fresh install — defaults already include these fields

    doc = frappe.get_doc("CRM Fields Layout", name)
    try:
        layout = json.loads(doc.layout or "[]")
    except (ValueError, TypeError):
        return
    if not isinstance(layout, list) or not layout:
        return

    existing = set()
    target = {"column": None}

    def scan_columns(columns):
        for col in columns or []:
            if isinstance(col.get("fields"), list):
                existing.update(col["fields"])
                if target["column"] is None:
                    target["column"] = col

    def scan_sections(sections):
        for sec in sections or []:
            scan_columns(sec.get("columns"))

    if "sections" in layout[0]:               # tabbed (Deal)
        for tab in layout:
            scan_sections(tab.get("sections"))
    else:                                      # flat (Lead)
        scan_sections(layout)

    if target["column"] is None:
        return
    missing = [f for f in FIELDS_TO_ADD if f not in existing]
    if not missing:
        return

    target["column"]["fields"].extend(missing)
    doc.layout = json.dumps(layout)
    doc.save(ignore_permissions=True)
    frappe.clear_cache(doctype=doctype)
