"""
crm/api/lifecycle.py — Deal lifecycle aggregator (opt-in → contract → finance)

Story:  oh-s1-2 (epic-optin-handoff)

Reverse-resolves the full CareVerse lifecycle chain for a single CRM Deal so the
exec pick-up surfaces (oh-s2-2 Deal Contracting panel, oh-s4-1 Finance AR) can
render a live status strip in one round-trip instead of six.

Rules enforced:
- @frappe.whitelist() on the public API.
- frappe.get_list() for every SELECT — no frappe.db.sql() SELECTs, no frappe.get_all().
- No ignore_permissions: gated by the caller's CRM Deal read permission
  (mirrors crm/api/activities.py:get_deal_activities), and every sub-resource
  read is independently permission-scoped by get_list. A caller who can read the
  Deal but not a sub-doctype (e.g. a Sales User vs the Network-Coordinator-scoped
  CRM Opt-In Submission) sees that link as None rather than an exception.
- No f-strings in log/error messages — % formatting only.
"""
from __future__ import annotations

import frappe
from frappe import _


@frappe.whitelist()
def get_deal_lifecycle(deal: str) -> dict:
    """
    Return the resolved lifecycle chain for one CRM Deal:

        {
          "submission":    {"ref", "status"} | None,
          "quotation":     {"name", "status", "docstatus", "grand_total"} | None,
          "contract":      {"name", "status", "workflow_state"} | None,
          "signatories":   [{"role", "status", "signed_at", "name", "email"}],
          "onboarding":    {"name", "approval_status", "n1", "n2", "tiberbu"} | None,
          "sales_invoice": {"name", "docstatus", "outstanding"} | None,
        }

    Missing links resolve to None (or [] for signatories); an incomplete chain
    never raises. Scoped by the caller's CRM Deal read permission.
    """
    # Gate on Deal read — mirrors crm/api/activities.py:get_deal_activities.
    if not frappe.has_permission("CRM Deal", "read", deal):
        frappe.throw(_("Not permitted"), frappe.PermissionError)

    quotation = _resolve_quotation(deal)
    contract = _resolve_contract(deal)

    return {
        "submission": _resolve_submission(deal),
        "quotation": quotation,
        "contract": contract,
        "signatories": _resolve_signatories(contract["name"] if contract else None),
        "onboarding": _resolve_onboarding(deal),
        "sales_invoice": _resolve_sales_invoice(quotation["name"] if quotation else None),
    }


# ---------------------------------------------------------------------------
# Private resolvers — each is a permission-scoped frappe.get_list() read.
# ---------------------------------------------------------------------------


def _can_read(doctype: str) -> bool:
    """True if the caller has doctype-level read — prevents get_list from raising."""
    return bool(frappe.has_permission(doctype, "read"))


def _resolve_submission(deal: str) -> dict | None:
    if not _can_read("CRM Opt-In Submission"):
        return None
    rows = frappe.get_list(
        "CRM Opt-In Submission",
        filters={"deal": deal},
        fields=["name", "status"],
        order_by="creation desc",
        limit=1,
    )
    if not rows:
        return None
    return {"ref": rows[0].name, "status": rows[0].status}


def _resolve_quotation(deal: str) -> dict | None:
    if not _can_read("Quotation"):
        return None
    rows = frappe.get_list(
        "Quotation",
        filters={"crm_deal": deal},
        fields=["name", "status", "docstatus", "grand_total"],
        order_by="creation desc",
        limit=1,
    )
    if not rows:
        return None
    r = rows[0]
    return {
        "name": r.name,
        "status": r.status,
        "docstatus": r.docstatus,
        "grand_total": r.grand_total,
    }


def _resolve_contract(deal: str) -> dict | None:
    if not _can_read("CRM Contract"):
        return None
    rows = frappe.get_list(
        "CRM Contract",
        filters={"deal": deal},
        fields=["name", "status", "workflow_state"],
        order_by="creation desc",
        limit=1,
    )
    if not rows:
        return None
    r = rows[0]
    return {"name": r.name, "status": r.status, "workflow_state": r.workflow_state}


def _resolve_signatories(contract: str | None) -> list:
    """Read signatory child rows off the parent Contract.

    frappe.get_list() on a child DocType silently drops non-standard fields
    (it returns `name` only), so we load the parent and read its child table —
    a permission-respecting single-document read, not get_all()/db.sql().
    """
    if not contract or not _can_read("CRM Contract"):
        return []
    doc = frappe.get_doc("CRM Contract", contract)
    return [
        {
            "role": r.signatory_role,
            "status": r.status,
            "signed_at": r.signed_at,
            "name": r.signatory_name,
            "email": r.signatory_email,
        }
        for r in doc.signatories
    ]


def _resolve_onboarding(deal: str) -> dict | None:
    if not _can_read("CRM Onboarding Request"):
        return None
    rows = frappe.get_list(
        "CRM Onboarding Request",
        filters={"deal": deal},
        fields=[
            "name",
            "approval_status",
            "network_approver_1_approved",
            "network_approver_2_approved",
            "tiberbu_approver_approved",
        ],
        order_by="creation desc",
        limit=1,
    )
    if not rows:
        return None
    r = rows[0]
    return {
        "name": r.name,
        "approval_status": r.approval_status,
        "n1": r.network_approver_1_approved,
        "n2": r.network_approver_2_approved,
        "tiberbu": r.tiberbu_approver_approved,
    }


def _resolve_sales_invoice(quotation: str | None) -> dict | None:
    if not quotation or not _can_read("Sales Invoice"):
        return None
    rows = frappe.get_list(
        "Sales Invoice",
        filters={"crm_quotation": quotation},
        fields=["name", "docstatus", "outstanding_amount"],
        order_by="creation desc",
        limit=1,
    )
    if not rows:
        return None
    r = rows[0]
    return {"name": r.name, "docstatus": r.docstatus, "outstanding": r.outstanding_amount}
