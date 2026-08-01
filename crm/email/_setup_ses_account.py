"""One-shot setup helper: create the CRM SES Outbound dummy Email Account.

Inserted via raw SQL to bypass the EmailAccount.validate_smtp_conn() check,
which would attempt a live TCP connection to localhost:25.  The account is
never used for SMTP — override_email_send intercepts every send before any
SMTP session is opened.
"""
import frappe
from frappe.utils import now_datetime


def create():
    if frappe.db.exists("Email Account", "CRM SES Outbound"):
        print("Email Account 'CRM SES Outbound' already exists — skipping.")
        return

    now = now_datetime()
    # SYSTEM-INTERNAL: raw SQL bypasses validate_smtp_conn; account is a
    # placeholder — SMTP is never opened because override_email_send fires first.
    frappe.db.sql(
        """
        INSERT INTO `tabEmail Account`
            (name, email_account_name, email_id,
             enable_outgoing, default_outgoing,
             smtp_server, smtp_port, use_tls, use_ssl,
             enable_incoming,
             creation, modified, modified_by, owner, docstatus)
        VALUES
            ('CRM SES Outbound', 'CRM SES Outbound', 'no-reply@tiberbu.com',
             1, 1,
             'localhost', 25, 0, 0,
             0,
             %s, %s, 'Administrator', 'Administrator', 0)
        """,
        (now, now),
    )
    frappe.db.commit()
    print("Created Email Account: CRM SES Outbound")
