"""
Extend ERPNext Quotation with CareVerse-specific custom fields so that
CRM Quote functionality can be migrated to the native ERPNext Quotation
doctype (Option B).

Also:
- Adds display fields (facility_name, package_tier) to Quotation Item.
- Updates Sales Invoice.crm_quote link target from CRM Quote → Quotation
  and renames the field to crm_quotation for clarity.
"""
import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
    # ── Quotation header fields ───────────────────────────────────────────────
    create_custom_fields(
        {
            "Quotation": [
                # CRM linkage
                {
                    "fieldname": "crm_section",
                    "fieldtype": "Section Break",
                    "label": "CareVerse CRM",
                    "insert_after": "party_name",
                    "collapsible": 1,
                },
                {
                    "fieldname": "crm_deal",
                    "fieldtype": "Link",
                    "label": "CRM Deal",
                    "options": "CRM Deal",
                    "insert_after": "crm_section",
                    "read_only": 0,
                    "no_copy": 1,
                    "in_list_view": 0,
                },
                {
                    "fieldname": "crm_partner",
                    "fieldtype": "Link",
                    "label": "CRM Partner",
                    "options": "CRM Partner",
                    "insert_after": "crm_deal",
                    "read_only": 0,
                    "no_copy": 1,
                },
                {
                    "fieldname": "crm_col_break",
                    "fieldtype": "Column Break",
                    "insert_after": "crm_partner",
                },
                {
                    "fieldname": "crm_payment_terms",
                    "fieldtype": "Select",
                    "label": "Payment Terms",
                    "options": "\nAnnual Upfront\nQuarterly Advance\nMonthly",
                    "default": "Annual Upfront",
                    "insert_after": "crm_col_break",
                },
                {
                    "fieldname": "contract_term_yrs",
                    "fieldtype": "Int",
                    "label": "Contract Term (Years)",
                    "default": "1",
                    "insert_after": "crm_payment_terms",
                },
                {
                    "fieldname": "contract_start_date",
                    "fieldtype": "Date",
                    "label": "Contract Start Date",
                    "insert_after": "contract_term_yrs",
                },
                # Sent-state flag (Quotation has no native "Sent" lifecycle state)
                {
                    "fieldname": "crm_sent",
                    "fieldtype": "Check",
                    "label": "Sent to Customer",
                    "default": "0",
                    "insert_after": "contract_start_date",
                    "read_only": 1,
                    "no_copy": 1,
                },
                # Revision chain
                {
                    "fieldname": "previous_version",
                    "fieldtype": "Link",
                    "label": "Previous Version",
                    "options": "Quotation",
                    "insert_after": "crm_sent",
                    "read_only": 1,
                    "no_copy": 1,
                },
                # CRM pricing summary (mirroring CRM Quote totals; read-only, computed by save_quote)
                {
                    "fieldname": "crm_totals_section",
                    "fieldtype": "Section Break",
                    "label": "CRM Pricing Summary",
                    "insert_after": "previous_version",
                    "collapsible": 1,
                },
                {
                    "fieldname": "discount_applied",
                    "fieldtype": "Currency",
                    "label": "Discount Applied",
                    "options": "currency",
                    "insert_after": "crm_totals_section",
                    "read_only": 1,
                    "no_copy": 1,
                },
                {
                    "fieldname": "vat_amount",
                    "fieldtype": "Currency",
                    "label": "VAT Amount (16%)",
                    "options": "currency",
                    "insert_after": "discount_applied",
                    "read_only": 1,
                    "no_copy": 1,
                },
                # Renewal schedule — reuses the existing CRM Quote Renewal Schedule child doctype
                {
                    "fieldname": "renewal_schedule_section",
                    "fieldtype": "Section Break",
                    "label": "Renewal Schedule",
                    "insert_after": "vat_amount",
                    "collapsible": 1,
                },
                {
                    "fieldname": "renewal_schedule",
                    "fieldtype": "Table",
                    "label": "Renewal Schedule",
                    "options": "CRM Quote Renewal Schedule",
                    "insert_after": "renewal_schedule_section",
                    "no_copy": 0,
                },
            ],

            # ── Quotation Item display fields ─────────────────────────────────
            "Quotation Item": [
                {
                    "fieldname": "facility_name",
                    "fieldtype": "Data",
                    "label": "Facility",
                    "insert_after": "item_name",
                    "no_copy": 0,
                    "in_list_view": 0,
                },
                {
                    "fieldname": "package_tier",
                    "fieldtype": "Select",
                    "label": "Package Tier",
                    "options": "\nCore\nAdvanced\nEnterprise",
                    "insert_after": "facility_name",
                    "no_copy": 0,
                    "in_list_view": 0,
                },
            ],
        },
        ignore_validate=True,
    )

    # ── Migrate Sales Invoice.crm_quote → crm_quotation (Link → Quotation) ──────
    # The old patch (create_custom_fields_for_quote_invoice_link) created
    # Sales Invoice.crm_quote as Link → CRM Quote. Now that quotes live in
    # ERPNext Quotation, the field must point at Quotation instead.
    #
    # Strategy:
    #   1. Rename the DB column (crm_quote → crm_quotation) if needed.
    #   2. Delete the stale Custom Field record (Sales Invoice-crm_quote).
    #   3. Recreate it cleanly as Sales Invoice-crm_quotation via create_custom_fields.

    # Step 1 — rename DB column if crm_quote still exists
    has_old_col = frappe.db.sql(
        "SHOW COLUMNS FROM `tabSales Invoice` LIKE 'crm_quote'"
    )
    has_new_col = frappe.db.sql(
        "SHOW COLUMNS FROM `tabSales Invoice` LIKE 'crm_quotation'"
    )
    if has_old_col and not has_new_col:
        frappe.db.sql(
            "ALTER TABLE `tabSales Invoice` "
            "CHANGE `crm_quote` `crm_quotation` VARCHAR(140) NULL DEFAULT NULL"
        )

    # Step 2 — remove stale Custom Field record (named after the old fieldname)
    for stale in ("Sales Invoice-crm_quote",):
        if frappe.db.exists("Custom Field", stale):
            frappe.db.delete("Custom Field", {"name": stale})

    frappe.db.commit()

    # Step 3 — create the correct Custom Field (skip if it already exists)
    from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
    create_custom_fields(
        {
            "Sales Invoice": [
                {
                    "fieldname": "crm_quotation",
                    "label": "CRM Quotation",
                    "fieldtype": "Link",
                    "options": "Quotation",
                    "insert_after": "crm_deal",
                    "read_only": 1,
                    "no_copy": 1,
                },
            ]
        },
        ignore_validate=True,
    )

    frappe.clear_cache()
