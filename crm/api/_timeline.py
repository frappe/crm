"""
crm/api/_timeline.py — Deal transition timeline helper

Story: oh-s1-3 (epic-optin-handoff)

Writes a Comment against a CRM Deal at each lifecycle transition (OIS processed,
contract generated, both-signed, fully executed, invoice posted) so a sales exec
sees the whole opt-in → contract → finance hand-off as one activity trail on the
Deal.

comment_type is "Comment" (not "Info") on purpose: Frappe routes "Info" comments
into docinfo.info_logs, a bucket that frappe/crm's crm.api.activities.
get_deal_activities never reads, so an "Info" entry is invisible in the CRM Deal
timeline (it surfaces only in Frappe Desk). "Comment" lands in docinfo.comments,
which get_deal_activities renders in the Activity/Comments feed.

Rules enforced:
- No f-strings in log text — callers pass %-formatted strings (see AC-03).
- ignore_permissions=True: this is a system-authored audit event that must be
  recorded regardless of the actor — including the guest contract-signing path,
  which already persists with ignore_permissions=True in crm/api/contracts.py.
- Best-effort: a logging failure must never abort the business transition.
"""
from __future__ import annotations

import frappe


def log_deal_event(deal: str, text: str) -> None:
    """Write an Info Comment on a CRM Deal. Never raises — logging is best-effort."""
    if not deal or not text:
        return
    try:
        frappe.get_doc(
            {
                "doctype": "Comment",
                "comment_type": "Comment",
                "reference_doctype": "CRM Deal",
                "reference_name": deal,
                "content": text,
            }
        ).insert(ignore_permissions=True)  # SYSTEM-INTERNAL: system-authored transition audit log
    except Exception:
        frappe.log_error(
            frappe.get_traceback(),
            "log_deal_event: failed to write timeline comment for deal %s" % deal,
        )
