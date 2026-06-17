"""Place the enriched fields next to their logically-related fields in the "Data"
tab, instead of stacking them in one column.

The earlier patch appended company_description / linkedin / twitter / key_people to
the first column it found, leaving that column overloaded and the others empty
(visible whitespace). Here we lift those four out and re-insert each right after the
field it belongs with — description by the organization, the social links by the
website, key people by the record owner — so related fields sit together and the
columns stay balanced. No new section. Idempotent.
"""

import json
import re

import frappe

# (field to place, predicate picking the field to place it after). Order matters:
# linkedin is inserted before twitter so the two social links chain together.
PLACEMENTS = [
    ("company_description", lambda f: f == "organization"),
    ("linkedin", lambda f: f == "website"),
    ("twitter", lambda f: f == "linkedin"),
    ("key_people", lambda f: bool(re.search(r"_owner$", f))),
]
GROUP_FIELDS = [field for field, _ in PLACEMENTS]
DOCTYPES = ("CRM Lead", "CRM Deal")


def _all_columns(layout):
    cols = []
    if "sections" in layout[0]:                       # tabbed (Deal)
        for tab in layout:
            for sec in tab.get("sections", []):
                cols.extend(sec.get("columns") or [])
    else:                                              # flat (Lead)
        for sec in layout:
            cols.extend(sec.get("columns") or [])
    return [c for c in cols if isinstance(c.get("fields"), list)]


def _place(columns, field, anchor_pred):
    for col in columns:
        for i, existing in enumerate(col["fields"]):
            if anchor_pred(existing):
                col["fields"].insert(i + 1, field)
                return
    # No anchor anywhere — drop it into the shortest column to keep balance.
    shortest = min(columns, key=lambda c: len(c["fields"]))
    shortest["fields"].append(field)


def execute():
    for doctype in DOCTYPES:
        _regroup(doctype)


def _regroup(doctype):
    name = frappe.db.get_value(
        "CRM Fields Layout", {"dt": doctype, "type": "Data Fields"})
    if not name:
        return

    doc = frappe.get_doc("CRM Fields Layout", name)
    try:
        layout = json.loads(doc.layout or "[]")
    except (ValueError, TypeError):
        return
    if not isinstance(layout, list) or not layout:
        return

    columns = _all_columns(layout)
    if not columns:
        return

    # Remove the four fields from wherever they currently are…
    for col in columns:
        col["fields"] = [f for f in col["fields"] if f not in GROUP_FIELDS]
    # …then re-insert each next to its logical anchor.
    for field, anchor_pred in PLACEMENTS:
        _place(columns, field, anchor_pred)

    doc.layout = json.dumps(layout)
    doc.save(ignore_permissions=True)
    frappe.clear_cache(doctype=doctype)
