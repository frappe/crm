"""Surface the enriched fields in the CRM side panel for existing installs.

Website Intelligence fills `organization_logo` (and, on Deal, industry/email/
mobile_no) but custom fields never auto-appear in the CRM side panel — it only
renders fields listed in the per-doctype `CRM Fields Layout` (type "Side Panel").

Fresh installs get the updated layouts from `install.add_default_fields_layout`.
This patch brings EXISTING side-panel layouts up to date, appending only the
fields that are missing so any user customizations are preserved. Idempotent.
"""

import json

import frappe

# Fields to ensure are present in each doctype's side panel. (Lead already shows
# organization/industry/email/mobile_no by default, so it only needs the logo.)
_EXTRAS = ["linkedin", "twitter"]
FIELDS_TO_ADD = {
    "CRM Lead": ["company_description", "no_of_employees"] + _EXTRAS,
    "CRM Deal": ["company_description", "industry", "no_of_employees"] + _EXTRAS,
    "CRM Organization": ["company_description"] + _EXTRAS,
}


def execute():
    for doctype, fields in FIELDS_TO_ADD.items():
        _add_fields_to_side_panel(doctype, fields)


def _add_fields_to_side_panel(doctype, fields):
    name = frappe.db.get_value(
        "CRM Fields Layout", {"dt": doctype, "type": "Side Panel"}
    )
    if not name:
        return  # fresh install — defaults already include these fields

    doc = frappe.get_doc("CRM Fields Layout", name)
    try:
        layout = json.loads(doc.layout or "[]")
    except (ValueError, TypeError):
        return
    if not isinstance(layout, list):
        return

    # Gather every fieldname already in the layout, and pick the first real
    # column to append to (e.g. Deal's first section "Contacts" has no columns,
    # so the target becomes "Organization Details").
    existing = set()
    target_column = None
    for section in layout:
        for col in section.get("columns") or []:
            if isinstance(col.get("fields"), list):
                existing.update(col["fields"])
                if target_column is None:
                    target_column = col
    if target_column is None:
        return

    missing = [f for f in fields if f not in existing]
    if not missing:
        return  # idempotent: already present

    target_column["fields"].extend(missing)
    doc.layout = json.dumps(layout)
    doc.save(ignore_permissions=True)
    frappe.clear_cache(doctype=doctype)
