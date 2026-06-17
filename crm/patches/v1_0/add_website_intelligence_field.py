"""Add the `website_intelligence` child table to CRM Lead and CRM Organization.

Idempotent: `create_custom_fields` skips fields that already exist, so this is
safe to run on every migrate.
"""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
    create_website_intelligence_custom_fields()


def create_website_intelligence_custom_fields():
    field = {
        "fieldname": "website_intelligence",
        "label": "Website Intelligence",
        "fieldtype": "Table",
        "options": "CRM Website Intelligence",
        "insert_after": "website",
        "read_only": 1,
        "no_copy": 1,
        "description": "Auto-generated enrichment runs from the company website.",
    }
    # CRM Organization already ships an `organization_logo` field. CRM Lead and
    # CRM Deal don't, so add one to hold the enriched company logo.
    org_logo = {
        "fieldname": "organization_logo",
        "label": "Organization Logo",
        "fieldtype": "Attach Image",
        "insert_after": "website",
        "no_copy": 1,
        "description": "Company logo discovered by Website Intelligence.",
    }
    # No description field exists natively on Lead/Deal/Org — add one to hold the
    # enriched company description.
    company_description = {
        "fieldname": "company_description",
        "label": "Company Description",
        "fieldtype": "Small Text",
        "insert_after": "organization_logo",
        "no_copy": 1,
        "description": "Company description discovered by Website Intelligence.",
    }

    # Enriched social links, business signals and key people — surfaced in the CRM
    # side panel (a child table can't render there). All discovered from the
    # company's own website.
    enrichment_extras = [
        {"fieldname": "linkedin", "label": "LinkedIn", "fieldtype": "Data",
         "insert_after": "company_description", "no_copy": 1},
        {"fieldname": "twitter", "label": "X (Twitter)", "fieldtype": "Data",
         "insert_after": "linkedin", "no_copy": 1},
        {"fieldname": "key_people", "label": "Key People", "fieldtype": "Small Text",
         "insert_after": "twitter", "no_copy": 1,
         "description": "Team members discovered by Website Intelligence."},
    ]

    common = [dict(field), dict(company_description)] + [dict(f) for f in enrichment_extras]
    create_custom_fields(
        {
            "CRM Lead": [dict(org_logo)] + common,
            "CRM Organization": list(common),
            "CRM Deal": [dict(org_logo)] + common,
        },
        ignore_validate=True,
    )
    for dt in ("CRM Lead", "CRM Organization", "CRM Deal"):
        frappe.clear_cache(doctype=dt)
