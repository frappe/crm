import frappe
from frappe.utils import today, get_first_day
from datetime import date


@frappe.whitelist()
def get_accessible_companies():
    return frappe.get_list(
        "Company",
        fields=["name", "abbr", "default_currency"],
        order_by="name asc",
    )


def _get_date_filter(period):
    """Return (from_date, to_date) for the given period string."""
    t = today()
    t_date = date.fromisoformat(t)
    if period == "quarter":
        month = t_date.month
        q_start = ((month - 1) // 3) * 3 + 1
        from_date = date(t_date.year, q_start, 1).isoformat()
        to_date = t
    elif period in ("year", "ytd"):
        from_date = date(t_date.year, 1, 1).isoformat()
        to_date = t
    else:  # month (default)
        from_date = get_first_day(t)
        to_date = t
    return from_date, to_date


def _is_admin(roles):
    return "System Manager" in roles or frappe.session.user == "Administrator"


def _has_ar_access(roles):
    return _is_admin(roles) or bool({"Finance Manager", "AR Accountant"} & set(roles))


def _has_ap_access(roles):
    return _is_admin(roles) or bool({"Finance Manager", "AP Accountant"} & set(roles))


def _company_currency(company):
    """Return the default currency for the company."""
    rows = frappe.get_list(
        "Company",
        filters=[["name", "=", company]],
        fields=["default_currency"],
        limit=1,
    )
    return rows[0].default_currency if rows else ""


def _get_ar_outstanding(company, currency):
    rows = frappe.get_list(
        "Sales Invoice",
        filters=[
            ["company", "=", company],
            ["docstatus", "=", 1],
            ["outstanding_amount", ">", 0],
        ],
        fields=[{"SUM": "outstanding_amount", "as": "total"}],
        limit=1,
    )
    total = rows[0].total if rows else 0
    return {"value": float(total or 0), "currency": currency, "delta_pct": 0, "delta_direction": "neutral"}


def _get_ar_overdue(company, currency):
    rows = frappe.get_list(
        "Sales Invoice",
        filters=[
            ["company", "=", company],
            ["docstatus", "=", 1],
            ["outstanding_amount", ">", 0],
            ["due_date", "<", today()],
        ],
        fields=[{"SUM": "outstanding_amount", "as": "total"}],
        limit=1,
    )
    total = rows[0].total if rows else 0
    return {"value": float(total or 0), "currency": currency, "delta_pct": 0, "delta_direction": "neutral"}


def _get_invoiced_mtd(company, currency, date_filter):
    from_date, to_date = date_filter
    rows = frappe.get_list(
        "Sales Invoice",
        filters=[
            ["company", "=", company],
            ["docstatus", "=", 1],
            ["posting_date", ">=", from_date],
            ["posting_date", "<=", to_date],
        ],
        fields=[{"SUM": "grand_total", "as": "total"}],
        limit=1,
    )
    total = rows[0].total if rows else 0
    return {"value": float(total or 0), "currency": currency, "delta_pct": 0, "delta_direction": "neutral"}


def _get_collected_mtd(company, currency, date_filter):
    from_date, to_date = date_filter
    rows = frappe.get_list(
        "Payment Entry",
        filters=[
            ["company", "=", company],
            ["docstatus", "=", 1],
            ["payment_type", "=", "Receive"],
            ["posting_date", ">=", from_date],
            ["posting_date", "<=", to_date],
        ],
        fields=[{"SUM": "paid_amount", "as": "total"}],
        limit=1,
    )
    total = rows[0].total if rows else 0
    return {"value": float(total or 0), "currency": currency, "delta_pct": 0, "delta_direction": "neutral"}


def _get_ap_outstanding(company, currency):
    rows = frappe.get_list(
        "Purchase Invoice",
        filters=[
            ["company", "=", company],
            ["docstatus", "=", 1],
            ["outstanding_amount", ">", 0],
        ],
        fields=[{"SUM": "outstanding_amount", "as": "total"}],
        limit=1,
    )
    total = rows[0].total if rows else 0
    return {"value": float(total or 0), "currency": currency, "delta_pct": 0, "delta_direction": "neutral"}


def _get_ap_overdue(company, currency):
    rows = frappe.get_list(
        "Purchase Invoice",
        filters=[
            ["company", "=", company],
            ["docstatus", "=", 1],
            ["outstanding_amount", ">", 0],
            ["due_date", "<", today()],
        ],
        fields=[{"SUM": "outstanding_amount", "as": "total"}],
        limit=1,
    )
    total = rows[0].total if rows else 0
    return {"value": float(total or 0), "currency": currency, "delta_pct": 0, "delta_direction": "neutral"}


def _get_pending_rebates(company, roles):
    # CRM Partner Rebate Voucher does not exist yet in Sprint 1 — return 0 stub
    return {"value": 0, "currency": "", "delta_pct": 0, "delta_direction": "neutral"}


def _get_unpaid_commissions(company, roles):
    # CRM Sales Commission does not exist yet in Sprint 1 — return 0 stub
    return {"value": 0, "currency": "", "delta_pct": 0, "delta_direction": "neutral"}


@frappe.whitelist()
def get_finance_kpis(company=None, period="month", force=0):
    company = company or frappe.defaults.get_user_default("company")
    frappe.has_permission("Company", doc=company, ptype="read", throw=True)
    roles = frappe.get_roles(frappe.session.user)
    cache_key = "fc_kpis_%s_%s_%s" % (frappe.session.user, company, period)
    if not frappe.utils.cint(force):
        cached = frappe.cache().get_value(cache_key)
        if cached:
            return cached
    result = {}
    currency = _company_currency(company)
    date_filter = _get_date_filter(period)
    if _has_ar_access(roles):
        result["ar_outstanding"] = _get_ar_outstanding(company, currency)
        result["ar_overdue"] = _get_ar_overdue(company, currency)
        result["invoiced_mtd"] = _get_invoiced_mtd(company, currency, date_filter)
        result["collected_mtd"] = _get_collected_mtd(company, currency, date_filter)
    if _has_ap_access(roles):
        result["ap_outstanding"] = _get_ap_outstanding(company, currency)
        result["ap_overdue"] = _get_ap_overdue(company, currency)
    result["pending_rebates"] = _get_pending_rebates(company, roles)
    result["unpaid_commissions"] = _get_unpaid_commissions(company, roles)
    frappe.cache().set_value(cache_key, result, expires_in_sec=300)
    return result
