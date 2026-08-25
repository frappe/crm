"""
crm/patches/v1_0/add_optin_crm_lead_fields.py

Story: optin-s1-1
Add custom columns required by the Opt-In portal to tabCRM Lead.
CRM Lead is a core frappe/crm DocType — schema changes must be DDL only;
we cannot ship them via the DocType JSON without forking a core file.

Idempotent: SHOW COLUMNS guard prevents duplicate ALTER TABLE on re-migrate.
"""
from __future__ import annotations

import frappe


def _add_column_if_missing(table, fieldname, field_def):
    """ALTER TABLE only when the column does not already exist."""
    existing = frappe.db.sql(
        "SHOW COLUMNS FROM `%s` LIKE '%s'" % (table, fieldname)
    )
    if not existing:
        frappe.db.sql(
            "ALTER TABLE `%s` ADD COLUMN `%s` %s" % (table, fieldname, field_def)
        )


def execute():
    table = "tabCRM Lead"
    columns = [
        ("optin_partial",           "tinyint(1) NOT NULL DEFAULT 0"),
        ("optin_resume_token_used", "tinyint(1) NOT NULL DEFAULT 0"),
        ("optin_link_expired",      "tinyint(1) NOT NULL DEFAULT 0"),
        ("optin_network_slug",      "varchar(140) DEFAULT NULL"),
        ("optin_source_url",        "varchar(255) DEFAULT NULL"),
        ("tc_accepted",             "tinyint(1) NOT NULL DEFAULT 0"),
        ("tc_document",             "varchar(140) DEFAULT NULL"),
        ("tc_document_hash",        "varchar(64) DEFAULT NULL"),
        ("tc_accepted_at",          "datetime DEFAULT NULL"),
        ("tc_ip_address",           "varchar(45) DEFAULT NULL"),
    ]
    for fieldname, field_def in columns:
        _add_column_if_missing(table, fieldname, field_def)
