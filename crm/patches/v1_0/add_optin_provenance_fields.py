"""
crm/patches/v1_0/add_optin_provenance_fields.py

Story: oh-s1-1 (epic-optin-handoff)

Promote the Opt-In provenance / T&C tracking attributes on CRM Lead — and the
CRM Deal -> CRM Opt-In Submission forward back-link — to first-class Custom
Fields so they are visible in frappe.get_meta() and, crucially, PERSISTED by
the ORM on doc.save()/insert().

Background: add_optin_crm_lead_fields.py added these as raw DDL columns only.
Raw columns are invisible to the DocType meta, so Document.db_insert() /
db_update() (which iterate meta.get_valid_columns()) never wrote to them and
crm/api/optin.py:_process_submission's lead.set(...) values were silently
dropped (gap D2). create_custom_fields() attaches proper DocFields AND
reconciles the pre-existing raw columns via frappe.db.updatedb (any widening,
e.g. varchar(64)->varchar(140), is lossless).

Idempotent: create_custom_fields() is a no-op when the fields already exist
(it diffs stored values before saving and swallows DuplicateEntryError).
"""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
    # SYSTEM-INTERNAL: patch path — schema provisioning for opt-in provenance.
    create_custom_fields(
        {
            "CRM Lead": [
                {
                    "fieldname": "optin_provenance_section",
                    "fieldtype": "Section Break",
                    "label": "Opt-In Provenance",
                    "insert_after": "source",
                    "collapsible": 1,
                },
                {
                    "fieldname": "optin_network_slug",
                    "fieldtype": "Data",
                    "label": "Opt-In Network Slug",
                    "insert_after": "optin_provenance_section",
                    "read_only": 1,
                    "no_copy": 1,
                },
                {
                    "fieldname": "tc_accepted",
                    "fieldtype": "Check",
                    "label": "T&C Accepted",
                    "insert_after": "optin_network_slug",
                    "read_only": 1,
                    "no_copy": 1,
                },
                {
                    "fieldname": "tc_document",
                    "fieldtype": "Data",
                    "label": "T&C Document",
                    "insert_after": "tc_accepted",
                    "read_only": 1,
                    "no_copy": 1,
                },
                {
                    "fieldname": "tc_document_hash",
                    "fieldtype": "Data",
                    "label": "T&C Document Hash (SHA-256)",
                    "insert_after": "tc_document",
                    "read_only": 1,
                    "no_copy": 1,
                    "length": 64,
                },
                {
                    "fieldname": "tc_accepted_at",
                    "fieldtype": "Datetime",
                    "label": "T&C Accepted At",
                    "insert_after": "tc_document_hash",
                    "read_only": 1,
                    "no_copy": 1,
                },
                {
                    "fieldname": "tc_ip_address",
                    "fieldtype": "Data",
                    "label": "T&C Acceptance IP",
                    "insert_after": "tc_accepted_at",
                    "read_only": 1,
                    "no_copy": 1,
                    "length": 45,
                },
            ],
            "CRM Deal": [
                {
                    "fieldname": "optin_submission",
                    "fieldtype": "Link",
                    "label": "Opt-In Submission",
                    "options": "CRM Opt-In Submission",
                    "insert_after": "status",
                    "read_only": 1,
                    "no_copy": 1,
                },
                {
                    "fieldname": "exec_notes",
                    "fieldtype": "Text",
                    "label": "Exec Notes",
                    "insert_after": "optin_submission",
                },
            ],
        }
    )
