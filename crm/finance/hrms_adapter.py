import frappe
from frappe.utils import nowdate


def is_hrms_installed():
    return "hrms" in frappe.get_installed_apps()


def get_expense_claims(company, filters=None, page=0, page_size=20):
    if not is_hrms_installed():
        return {"items": [], "hrms_not_installed": True}
    base_filters = [["company", "=", company]]
    if filters:
        base_filters.extend(filters)
    rows = frappe.get_list(
        "Expense Claim",
        fields=[
            "name", "employee", "employee_name", "department", "posting_date",
            "total_claimed_amount", "total_sanctioned_amount", "mode_of_payment",
            "status", "is_paid", "clearance_date",
        ],
        filters=base_filters,
        limit_page_length=int(page_size),
        limit_start=int(page) * int(page_size),
        order_by="posting_date desc",
    )
    return {"items": rows, "hrms_not_installed": False}


def get_employee_advances(company, filters=None, page=0, page_size=20):
    if not is_hrms_installed():
        return {"items": [], "hrms_not_installed": True}
    base_filters = [
        ["company", "=", company],
        ["status", "=", "Paid"],
        ["pending_amount", ">", 0],
    ]
    if filters:
        base_filters.extend(filters)
    rows = frappe.get_list(
        "Employee Advance",
        fields=[
            "name", "employee", "employee_name", "department", "posting_date",
            "advance_amount", "claimed_amount", "pending_amount", "status",
        ],
        filters=base_filters,
        limit_page_length=int(page_size),
        limit_start=int(page) * int(page_size),
        order_by="posting_date desc",
    )
    return {"items": rows, "hrms_not_installed": False}


def get_expense_journals(company, filters=None, page=0, page_size=20):
    # Journal Entry is a core ERPNext doctype — no HRMS dependency
    base_filters = [
        ["company", "=", company],
        ["docstatus", "!=", 2],
    ]
    if filters:
        base_filters.extend(filters)
    rows = frappe.get_list(
        "Journal Entry",
        fields=["name", "posting_date", "entry_type", "total_debit", "remark", "docstatus"],
        filters=base_filters,
        limit_page_length=int(page_size),
        limit_start=int(page) * int(page_size),
        order_by="posting_date desc",
    )
    return {"items": rows}


def mark_expense_claim_paid(name):
    if not is_hrms_installed():
        frappe.throw("HRMS is not installed")
    roles = frappe.get_roles(frappe.session.user)
    if not any(r in roles for r in ("Accounts User", "Accounts Manager", "Finance Manager", "System Manager")):
        frappe.throw("Insufficient permissions", frappe.PermissionError)
    frappe.db.set_value("Expense Claim", name, {
        "is_paid": 1,
        "clearance_date": nowdate(),
    })
    return {"status": "paid", "name": name}
