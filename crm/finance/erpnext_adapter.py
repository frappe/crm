"""
Transparent same-site / remote-site adapter for ERPNext DocType reads.

CRM-owned DocTypes (CRM Partner Rebate Voucher, CRM Sales Commission,
CRM Onboarding Request) NEVER go through this adapter — they always live on
the CRM site. Only ERPNext and HRMS DocTypes route through it.
"""

import frappe
from frappe.frappeclient import FrappeClient


_CRM_DOCTYPES = frozenset([
    "CRM Partner",
    "CRM Rebate Structure",
    "CRM Partner Rebate Voucher",
    "CRM Sales Commission",
    "CRM Onboarding Request",
    "CRM Lead",
    "CRM Deal",
    "CRM Organization",
])


def _get_settings():
    return frappe.get_single("ERPNext CRM Settings")


def _is_remote():
    try:
        s = _get_settings()
        return bool(s.enabled and s.is_erpnext_in_different_site)
    except Exception:
        return False


def _get_client():
    s = _get_settings()
    return FrappeClient(
        s.erpnext_site_url,
        api_key=s.api_key,
        api_secret=s.get_password("api_secret", raise_exception=False),
    )


def get_list(doctype, **kwargs):
    """Transparent frappe.get_list wrapper — routes remote when configured."""
    if doctype in _CRM_DOCTYPES:
        # CRM-owned DocTypes always stay on the local site
        return frappe.get_list(doctype, **kwargs)
    if _is_remote():
        client = _get_client()
        return client.get_list(doctype, **kwargs)
    return frappe.get_list(doctype, **kwargs)


def submit_doc(doctype, name):
    """Submit a document — same-site or remote."""
    if _is_remote():
        client = _get_client()
        doc = client.get_doc(doctype, name)
        doc["docstatus"] = 1
        return client.update(doc)
    doc = frappe.get_doc(doctype, name)
    doc.submit()
    return doc.as_dict()
