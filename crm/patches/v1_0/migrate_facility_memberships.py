"""
Migrate CRM Pre-Qualified Facility flat fields → CRM Facility Membership child rows.
Each existing facility row (with network + contact fields) gets one child membership row.
"""
import frappe


def execute():
    if not frappe.db.table_exists("CRM Pre-Qualified Facility"):
        return

    # Read old flat columns directly — they are being removed from the doctype but
    # still exist in MariaDB until we drop them (which we don't; Frappe leaves them).
    rows = frappe.db.sql(
        """SELECT name, network, status, contact_name, contact_email, contact_phone
           FROM `tabCRM Pre-Qualified Facility`
           WHERE network IS NOT NULL AND network != ''""",
        as_dict=True,
    )

    for row in rows:
        # Skip if a membership for this facility+network already exists
        existing = frappe.db.exists(
            "CRM Facility Membership",
            {"parent": row.name, "parenttype": "CRM Pre-Qualified Facility", "network": row.network},
        )
        if existing:
            continue

        child = frappe.new_doc("CRM Facility Membership")
        child.parent = row.name
        child.parenttype = "CRM Pre-Qualified Facility"
        child.parentfield = "memberships"
        child.network = row.network
        child.status = row.status or "Active"
        child.contact_name = row.contact_name or ""
        child.contact_email = row.contact_email or ""
        child.contact_phone = row.contact_phone or ""
        child.insert(ignore_permissions=True)  # SYSTEM-INTERNAL

    frappe.db.commit()
