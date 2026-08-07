import json
import calendar
import frappe
from frappe.utils import today, get_first_day, date_diff, add_months
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
    if not frappe.db.exists("DocType", "CRM Partner Rebate Voucher"):
        return {"value": 0, "currency": "", "delta_pct": 0, "delta_direction": "neutral"}
    currency = _company_currency(company)
    rows = frappe.get_list(
        "CRM Partner Rebate Voucher",
        filters=[["status", "=", "Pending"]],
        fields=[{"SUM": "rebate_amount", "as": "total"}],
        limit=1,
    )
    total = rows[0].total if rows else 0
    return {"value": float(total or 0), "currency": currency, "delta_pct": 0, "delta_direction": "neutral"}


def _get_unpaid_commissions(company, roles):
    if not frappe.db.exists("DocType", "CRM Sales Commission"):
        return {"value": 0, "currency": "", "delta_pct": 0, "delta_direction": "neutral"}
    currency = _company_currency(company)
    rows = frappe.get_list(
        "CRM Sales Commission",
        filters=[["status", "in", ["Reported", "Confirmed"]]],
        fields=[{"SUM": "commission_amount", "as": "total"}],
        limit=1,
    )
    total = rows[0].total if rows else 0
    return {"value": float(total or 0), "currency": currency, "delta_pct": 0, "delta_direction": "neutral"}


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


# ---------------------------------------------------------------------------
# fc-s2-1: Pending Actions Inbox
# ---------------------------------------------------------------------------

def _age(date_str):
    """Return age in days from a date string to today."""
    if not date_str:
        return 0
    try:
        return int(date_diff(today(), str(date_str)))
    except Exception:
        return 0


def _action_item(type_, doctype, docname, party_type, party_name, amount, currency,
                 age, urgency, primary_action, primary_action_label, secondary_actions=None,
                 erpnext_url=None):
    return {
        "type": type_,
        "doctype": doctype,
        "docname": docname,
        "party_type": party_type,
        "party_name": party_name,
        "amount": float(amount or 0),
        "currency": currency or "",
        "age_days": age,
        "urgency": urgency,
        "primary_action": primary_action,
        "primary_action_label": primary_action_label,
        "secondary_actions": secondary_actions or [],
        "erpnext_url": erpnext_url or ("/app/%s/%s" % (doctype.lower().replace(" ", "-"), docname)),
    }


def _collect_overdue_invoices(company, currency, roles):
    if not _has_ar_access(roles):
        return []
    rows = frappe.get_list(
        "Sales Invoice",
        filters=[
            ["company", "=", company],
            ["docstatus", "=", 1],
            ["outstanding_amount", ">", 0],
            ["due_date", "<", today()],
        ],
        fields=["name", "customer", "outstanding_amount", "due_date"],
        order_by="due_date asc",
        limit=50,
    )
    items = []
    for r in rows:
        age = _age(r.due_date)
        urgency = "critical" if age > 30 else "warning"
        items.append(_action_item(
            "overdue_invoice", "Sales Invoice", r.name,
            "Customer", r.customer, r.outstanding_amount, currency,
            age, urgency,
            "record_payment", "Record Payment",
            erpnext_url="/app/payment-entry/new-payment-entry-1?party_type=Customer&party=%s" % r.customer,
        ))
    return items


def _collect_unapplied_payments(company, currency, roles):
    if not _has_ar_access(roles):
        return []
    rows = frappe.get_list(
        "Payment Entry",
        filters=[
            ["company", "=", company],
            ["docstatus", "=", 1],
            ["payment_type", "=", "Receive"],
            ["unallocated_amount", ">", 0],
        ],
        fields=["name", "party", "unallocated_amount", "posting_date"],
        order_by="posting_date asc",
        limit=50,
    )
    items = []
    for r in rows:
        age = _age(r.posting_date)
        urgency = "warning" if age > 7 else "normal"
        items.append(_action_item(
            "unapplied_payment", "Payment Entry", r.name,
            "Customer", r.party, r.unallocated_amount, currency,
            age, urgency,
            "reconcile", "Reconcile",
        ))
    return items


def _collect_pending_rebates(company, currency, roles):
    if not frappe.db.exists("DocType", "CRM Partner Rebate Voucher"):
        return []
    if not (_has_ar_access(roles) or "Partner RM" in roles):
        return []
    base_filters = [["status", "=", "Pending"]]
    if "Partner RM" in roles and "Finance Manager" not in roles and "AR Accountant" not in roles:
        own_partners = frappe.get_list(
            "CRM Partner",
            filters={"partner_rm": frappe.session.user},
            pluck="name",
        )
        if not own_partners:
            return []
        base_filters.append(["partner", "in", own_partners])
    rows = frappe.get_list(
        "CRM Partner Rebate Voucher",
        filters=base_filters,
        fields=["name", "partner", "rebate_amount", "creation"],
        order_by="creation asc",
        limit=50,
    )
    items = []
    for r in rows:
        age = _age(r.creation)
        urgency = "warning" if age > 5 else "normal"
        items.append(_action_item(
            "pending_rebate", "CRM Partner Rebate Voucher", r.name,
            "Partner", r.partner, r.rebate_amount, currency,
            age, urgency,
            "approve", "Approve",
        ))
    return items


def _collect_approved_rebates_unpaid(company, currency, roles):
    if not frappe.db.exists("DocType", "CRM Partner Rebate Voucher"):
        return []
    if "Finance Manager" not in roles and not _is_admin(roles):
        return []
    rows = frappe.get_list(
        "CRM Partner Rebate Voucher",
        filters=[["status", "=", "Approved"]],
        fields=["name", "partner", "rebate_amount", "approved_date"],
        order_by="approved_date asc",
        limit=50,
    )
    items = []
    for r in rows:
        age = _age(r.approved_date)
        urgency = "warning" if age > 7 else "normal"
        items.append(_action_item(
            "approved_rebate_unpaid", "CRM Partner Rebate Voucher", r.name,
            "Partner", r.partner, r.rebate_amount, currency,
            age, urgency,
            "mark_paid", "Mark Paid",
        ))
    return items


def _collect_unconfirmed_commissions(company, currency, roles):
    if not frappe.db.exists("DocType", "CRM Sales Commission"):
        return []
    if not (_has_ar_access(roles) or "Sales Manager" in roles):
        return []
    base_filters = [["status", "=", "Reported"]]
    if "Sales Manager" in roles and "Finance Manager" not in roles and "AR Accountant" not in roles:
        # scope to own team — deals where deal_owner == session user for now
        base_filters.append(["deal", "in", frappe.get_list(
            "CRM Deal",
            filters={"deal_owner": frappe.session.user},
            pluck="name",
        ) or ["__none__"]])
    rows = frappe.get_list(
        "CRM Sales Commission",
        filters=base_filters,
        fields=["name", "sales_person", "commission_amount", "creation"],
        order_by="creation asc",
        limit=50,
    )
    items = []
    for r in rows:
        age = _age(r.creation)
        urgency = "warning" if age > 3 else "normal"
        items.append(_action_item(
            "unconfirmed_commission", "CRM Sales Commission", r.name,
            "User", r.sales_person, r.commission_amount, currency,
            age, urgency,
            "confirm", "Confirm",
        ))
    return items


def _collect_confirmed_commissions_unpaid(company, currency, roles):
    if not frappe.db.exists("DocType", "CRM Sales Commission"):
        return []
    if "Finance Manager" not in roles and not _is_admin(roles):
        return []
    rows = frappe.get_list(
        "CRM Sales Commission",
        filters=[["status", "=", "Confirmed"]],
        fields=["name", "sales_person", "commission_amount", "creation"],
        order_by="creation asc",
        limit=50,
    )
    items = []
    for r in rows:
        age = _age(r.creation)
        urgency = "warning" if age > 7 else "normal"
        items.append(_action_item(
            "confirmed_commission_unpaid", "CRM Sales Commission", r.name,
            "User", r.sales_person, r.commission_amount, currency,
            age, urgency,
            "mark_paid", "Mark Paid",
        ))
    return items


def _collect_expense_claims_pending_payment(company, currency, roles):
    if not _has_ap_access(roles):
        return []
    if not frappe.db.exists("DocType", "Expense Claim"):
        return []
    rows = frappe.get_list(
        "Expense Claim",
        filters=[
            ["company", "=", company],
            ["status", "=", "Approved"],
            ["is_paid", "=", 0],
        ],
        fields=["name", "employee_name", "total_sanctioned_amount", "posting_date"],
        order_by="posting_date asc",
        limit=50,
    )
    items = []
    for r in rows:
        age = _age(r.posting_date)
        urgency = "warning" if age > 5 else "normal"
        items.append(_action_item(
            "expense_claim_pending_payment", "Expense Claim", r.name,
            "Employee", r.employee_name, r.total_sanctioned_amount, currency,
            age, urgency,
            "mark_paid", "Mark Paid",
        ))
    return items


def _collect_employee_advances_unclaimed(company, currency, roles):
    if not _has_ap_access(roles):
        return []
    if not frappe.db.exists("DocType", "Employee Advance"):
        return []
    rows = frappe.get_list(
        "Employee Advance",
        filters=[
            ["company", "=", company],
            ["status", "=", "Paid"],
            ["pending_amount", ">", 0],
        ],
        fields=["name", "employee_name", "pending_amount", "posting_date"],
        order_by="posting_date asc",
        limit=50,
    )
    items = []
    for r in rows:
        age = _age(r.posting_date)
        urgency = "warning" if age > 30 else "normal"
        items.append(_action_item(
            "employee_advance_unclaimed", "Employee Advance", r.name,
            "Employee", r.employee_name, r.pending_amount, currency,
            age, urgency,
            "review", "Review",
        ))
    return items


def _collect_overdue_purchase_invoices(company, currency, roles):
    if not _has_ap_access(roles):
        return []
    rows = frappe.get_list(
        "Purchase Invoice",
        filters=[
            ["company", "=", company],
            ["docstatus", "=", 1],
            ["outstanding_amount", ">", 0],
            ["due_date", "<", today()],
        ],
        fields=["name", "supplier", "outstanding_amount", "due_date"],
        order_by="due_date asc",
        limit=50,
    )
    items = []
    for r in rows:
        age = _age(r.due_date)
        urgency = "critical" if age > 30 else "warning"
        items.append(_action_item(
            "overdue_purchase_invoice", "Purchase Invoice", r.name,
            "Supplier", r.supplier, r.outstanding_amount, currency,
            age, urgency,
            "record_payment", "Record Payment",
            erpnext_url="/app/payment-entry/new-payment-entry-1?party_type=Supplier&party=%s" % r.supplier,
        ))
    return items


def _collect_purchase_invoices_pending_approval(company, currency, roles):
    if "Finance Manager" not in roles and not _is_admin(roles):
        return []
    rows = frappe.get_list(
        "Purchase Invoice",
        filters=[
            ["company", "=", company],
            ["docstatus", "=", 0],
        ],
        fields=["name", "supplier", "grand_total", "creation"],
        order_by="creation asc",
        limit=50,
    )
    items = []
    for r in rows:
        age = _age(r.creation)
        items.append(_action_item(
            "purchase_invoice_pending_approval", "Purchase Invoice", r.name,
            "Supplier", r.supplier, r.grand_total, currency,
            age, "warning",
            "approve", "Approve",
        ))
    return items


def _collect_bank_transactions_unmatched(company, currency, roles):
    if not (_has_ar_access(roles) or _has_ap_access(roles)):
        return []
    if not frappe.db.exists("DocType", "Bank Transaction"):
        return []
    rows = frappe.get_list(
        "Bank Transaction",
        filters=[
            ["company", "=", company],
            ["status", "=", "Unreconciled"],
        ],
        fields=["name", "bank_account", "deposit", "withdrawal", "date"],
        order_by="date asc",
        limit=50,
    )
    items = []
    for r in rows:
        age = _age(r.date)
        urgency = "warning" if age > 3 else "normal"
        amount = float(r.deposit or 0) + float(r.withdrawal or 0)
        items.append(_action_item(
            "bank_transaction_unmatched", "Bank Transaction", r.name,
            "Bank Account", r.bank_account, amount, currency,
            age, urgency,
            "reconcile", "Reconcile",
            erpnext_url="/app/bank-reconciliation-tool?bank_account=%s" % r.bank_account,
        ))
    return items


def _collect_period_closing_due(currency, roles):
    if "Finance Manager" not in roles and not _is_admin(roles):
        return []
    # Check if a Period Closing Voucher exists for the current fiscal year
    if not frappe.db.exists("DocType", "Period Closing Voucher"):
        return []
    current_year = date.today().year
    existing = frappe.get_list(
        "Period Closing Voucher",
        filters=[["transaction_date", ">=", "%s-01-01" % current_year]],
        limit=1,
    )
    if existing:
        return []
    return [_action_item(
        "period_closing_due", "Period Closing Voucher", "new",
        "", "Current Fiscal Period", 0, currency,
        0, "critical",
        "create", "Create Period Closing",
        erpnext_url="/app/period-closing-voucher/new-period-closing-voucher-1",
    )]


def _collect_subscription_invoices_due(company, currency, roles):
    if not _has_ar_access(roles):
        return []
    if not frappe.db.exists("DocType", "Subscription"):
        return []
    # Use current_invoice_end as the invoice-due indicator (ERPNext v16 Subscription)
    meta = frappe.get_meta("Subscription")
    date_field = "current_invoice_end" if meta.has_field("current_invoice_end") else None
    if not date_field:
        return []
    rows = frappe.get_list(
        "Subscription",
        filters=[
            ["company", "=", company],
            ["status", "=", "Active"],
            [date_field, "<=", today()],
        ],
        fields=["name", "party", date_field],
        order_by=date_field + " asc",
        limit=50,
    )
    items = []
    for r in rows:
        due_date = r.get(date_field)
        age = _age(due_date)
        items.append(_action_item(
            "subscription_invoice_due", "Subscription", r.name,
            "Customer", r.party or "", 0, currency,
            age, "warning",
            "generate_invoice", "Generate Invoice",
        ))
    return items


_URGENCY_RANK = {"critical": 0, "warning": 1, "normal": 2}


@frappe.whitelist()
def get_pending_actions(company=None):
    company = company or frappe.defaults.get_user_default("company")
    frappe.has_permission("Company", doc=company, ptype="read", throw=True)
    roles = frappe.get_roles(frappe.session.user)
    currency = _company_currency(company)

    items = []
    items.extend(_collect_overdue_invoices(company, currency, roles))
    items.extend(_collect_unapplied_payments(company, currency, roles))
    items.extend(_collect_pending_rebates(company, currency, roles))
    items.extend(_collect_approved_rebates_unpaid(company, currency, roles))
    items.extend(_collect_unconfirmed_commissions(company, currency, roles))
    items.extend(_collect_confirmed_commissions_unpaid(company, currency, roles))
    items.extend(_collect_expense_claims_pending_payment(company, currency, roles))
    items.extend(_collect_employee_advances_unclaimed(company, currency, roles))
    items.extend(_collect_overdue_purchase_invoices(company, currency, roles))
    items.extend(_collect_purchase_invoices_pending_approval(company, currency, roles))
    items.extend(_collect_bank_transactions_unmatched(company, currency, roles))
    items.extend(_collect_period_closing_due(currency, roles))
    items.extend(_collect_subscription_invoices_due(company, currency, roles))

    items.sort(key=lambda x: (_URGENCY_RANK.get(x["urgency"], 2), -x["age_days"]))
    return items


# ---------------------------------------------------------------------------
# fc-s2-2: Receivables APIs
# ---------------------------------------------------------------------------

@frappe.whitelist()
def get_ar_invoices(company=None, filters=None, page=0, page_size=20):
    roles = frappe.get_roles(frappe.session.user)
    if not _has_ar_access(roles):
        frappe.throw("Insufficient permissions", frappe.PermissionError)
    company = company or frappe.defaults.get_user_default("company")
    frappe.has_permission("Company", doc=company, ptype="read", throw=True)
    base_filters = [
        ["company", "=", company],
        ["docstatus", "=", 1],
        ["outstanding_amount", ">", 0],
    ]
    if filters:
        if isinstance(filters, str):
            filters = json.loads(filters)
        base_filters.extend(filters)
    rows = frappe.get_list(
        "Sales Invoice",
        filters=base_filters,
        fields=["name", "customer", "posting_date", "due_date", "grand_total", "outstanding_amount", "status"],
        order_by="due_date asc",
        limit_page_length=int(page_size),
        limit_start=int(page) * int(page_size),
    )
    today_str = today()
    for r in rows:
        due = r.get("due_date")
        r["days_overdue"] = max(0, int(date_diff(today_str, str(due)))) if due else 0
    return rows


@frappe.whitelist()
def get_sales_orders(company=None, filters=None, page=0, page_size=20):
    roles = frappe.get_roles(frappe.session.user)
    if not _has_ar_access(roles):
        frappe.throw("Insufficient permissions", frappe.PermissionError)
    company = company or frappe.defaults.get_user_default("company")
    frappe.has_permission("Company", doc=company, ptype="read", throw=True)
    base_filters = [["company", "=", company], ["docstatus", "=", 1]]
    if filters:
        if isinstance(filters, str):
            filters = json.loads(filters)
        base_filters.extend(filters)
    return frappe.get_list(
        "Sales Order",
        filters=base_filters,
        fields=["name", "customer", "transaction_date", "grand_total", "status", "billing_status"],
        order_by="transaction_date desc",
        limit_page_length=int(page_size),
        limit_start=int(page) * int(page_size),
    )


@frappe.whitelist()
def get_customer_payments(company=None, filters=None, page=0, page_size=20):
    roles = frappe.get_roles(frappe.session.user)
    if not _has_ar_access(roles):
        frappe.throw("Insufficient permissions", frappe.PermissionError)
    company = company or frappe.defaults.get_user_default("company")
    frappe.has_permission("Company", doc=company, ptype="read", throw=True)
    base_filters = [
        ["company", "=", company],
        ["payment_type", "=", "Receive"],
        ["docstatus", "=", 1],
    ]
    if filters:
        if isinstance(filters, str):
            filters = json.loads(filters)
        base_filters.extend(filters)
    return frappe.get_list(
        "Payment Entry",
        filters=base_filters,
        fields=["name", "party", "posting_date", "paid_amount", "mode_of_payment",
                "allocated_amount", "unallocated_amount"],
        order_by="posting_date desc",
        limit_page_length=int(page_size),
        limit_start=int(page) * int(page_size),
    )


@frappe.whitelist()
def get_customers(company=None, page=0, page_size=20):
    roles = frappe.get_roles(frappe.session.user)
    if not _has_ar_access(roles):
        frappe.throw("Insufficient permissions", frappe.PermissionError)
    company = company or frappe.defaults.get_user_default("company")
    frappe.has_permission("Company", doc=company, ptype="read", throw=True)
    return frappe.get_list(
        "Customer",
        fields=["name", "customer_name", "customer_group", "territory"],
        order_by="customer_name asc",
        limit_page_length=int(page_size),
        limit_start=int(page) * int(page_size),
    )


# ---------------------------------------------------------------------------
# fc-s2-3: Payables APIs
# ---------------------------------------------------------------------------

@frappe.whitelist()
def get_ap_invoices(company=None, filters=None, page=0, page_size=20, include_draft=0):
    roles = frappe.get_roles(frappe.session.user)
    if not _has_ap_access(roles):
        frappe.throw("Insufficient permissions", frappe.PermissionError)
    company = company or frappe.defaults.get_user_default("company")
    frappe.has_permission("Company", doc=company, ptype="read", throw=True)
    base_filters = [["company", "=", company]]
    if frappe.utils.cint(include_draft):
        # Pending-approval view: draft invoices only
        base_filters.append(["docstatus", "=", 0])
    else:
        base_filters.extend([
            ["docstatus", "=", 1],
            ["outstanding_amount", ">", 0],
        ])
    if filters:
        if isinstance(filters, str):
            filters = json.loads(filters)
        base_filters.extend(filters)
    rows = frappe.get_list(
        "Purchase Invoice",
        filters=base_filters,
        fields=["name", "supplier", "posting_date", "due_date", "grand_total", "outstanding_amount", "status"],
        order_by="due_date asc",
        limit_page_length=int(page_size),
        limit_start=int(page) * int(page_size),
    )
    today_str = today()
    for r in rows:
        due = r.get("due_date")
        r["days_overdue"] = max(0, int(date_diff(today_str, str(due)))) if due else 0
    return rows


@frappe.whitelist()
def get_purchase_orders(company=None, filters=None, page=0, page_size=20):
    roles = frappe.get_roles(frappe.session.user)
    if not _has_ap_access(roles):
        frappe.throw("Insufficient permissions", frappe.PermissionError)
    company = company or frappe.defaults.get_user_default("company")
    frappe.has_permission("Company", doc=company, ptype="read", throw=True)
    base_filters = [["company", "=", company], ["docstatus", "=", 1]]
    if filters:
        if isinstance(filters, str):
            filters = json.loads(filters)
        base_filters.extend(filters)
    return frappe.get_list(
        "Purchase Order",
        filters=base_filters,
        fields=["name", "supplier", "transaction_date", "grand_total", "status", "billing_status"],
        order_by="transaction_date desc",
        limit_page_length=int(page_size),
        limit_start=int(page) * int(page_size),
    )


@frappe.whitelist()
def get_supplier_payments(company=None, filters=None, page=0, page_size=20):
    roles = frappe.get_roles(frappe.session.user)
    if not _has_ap_access(roles):
        frappe.throw("Insufficient permissions", frappe.PermissionError)
    company = company or frappe.defaults.get_user_default("company")
    frappe.has_permission("Company", doc=company, ptype="read", throw=True)
    base_filters = [
        ["company", "=", company],
        ["payment_type", "=", "Pay"],
        ["docstatus", "=", 1],
    ]
    if filters:
        if isinstance(filters, str):
            filters = json.loads(filters)
        base_filters.extend(filters)
    return frappe.get_list(
        "Payment Entry",
        filters=base_filters,
        fields=["name", "party", "posting_date", "paid_amount", "mode_of_payment",
                "allocated_amount", "unallocated_amount"],
        order_by="posting_date desc",
        limit_page_length=int(page_size),
        limit_start=int(page) * int(page_size),
    )


@frappe.whitelist()
def get_suppliers(company=None, page=0, page_size=20):
    roles = frappe.get_roles(frappe.session.user)
    if not _has_ap_access(roles):
        frappe.throw("Insufficient permissions", frappe.PermissionError)
    company = company or frappe.defaults.get_user_default("company")
    frappe.has_permission("Company", doc=company, ptype="read", throw=True)
    return frappe.get_list(
        "Supplier",
        fields=["name", "supplier_name", "supplier_group", "supplier_type"],
        order_by="supplier_name asc",
        limit_page_length=int(page_size),
        limit_start=int(page) * int(page_size),
    )


# ---------------------------------------------------------------------------
# fc-s3-2: Expenses APIs
# ---------------------------------------------------------------------------

@frappe.whitelist()
def get_expense_claims(company=None, filters=None, page=0, page_size=20):
    roles = frappe.get_roles(frappe.session.user)
    if not _has_ap_access(roles):
        frappe.throw("Insufficient permissions", frappe.PermissionError)
    company = company or frappe.defaults.get_user_default("company")
    frappe.has_permission("Company", doc=company, ptype="read", throw=True)
    from crm.finance.hrms_adapter import get_expense_claims as _get_claims
    if filters and isinstance(filters, str):
        filters = json.loads(filters)
    return _get_claims(company, filters or [], int(page), int(page_size))


@frappe.whitelist()
def get_employee_advances(company=None, filters=None, page=0, page_size=20):
    roles = frappe.get_roles(frappe.session.user)
    if not _has_ap_access(roles):
        frappe.throw("Insufficient permissions", frappe.PermissionError)
    company = company or frappe.defaults.get_user_default("company")
    frappe.has_permission("Company", doc=company, ptype="read", throw=True)
    from crm.finance.hrms_adapter import get_employee_advances as _get_advances
    if filters and isinstance(filters, str):
        filters = json.loads(filters)
    return _get_advances(company, filters or [], int(page), int(page_size))


@frappe.whitelist()
def get_expense_journals(company=None, filters=None, page=0, page_size=20):
    roles = frappe.get_roles(frappe.session.user)
    if not _has_ap_access(roles):
        frappe.throw("Insufficient permissions", frappe.PermissionError)
    company = company or frappe.defaults.get_user_default("company")
    frappe.has_permission("Company", doc=company, ptype="read", throw=True)
    from crm.finance.hrms_adapter import get_expense_journals as _get_journals
    if filters and isinstance(filters, str):
        filters = json.loads(filters)
    return _get_journals(company, filters or [], int(page), int(page_size))


@frappe.whitelist()
def mark_expense_claim_paid(name: str) -> dict:
    from crm.finance.hrms_adapter import mark_expense_claim_paid as _mark_paid
    return _mark_paid(name)


# ---------------------------------------------------------------------------
# fc-s3-3: Partner & Commission APIs
# ---------------------------------------------------------------------------

@frappe.whitelist()
def get_rebate_vouchers(company=None, filters=None, page=0, page_size=20):
    roles = frappe.get_roles(frappe.session.user)
    if not (_has_ar_access(roles) or "Partner RM" in roles):
        frappe.throw("Insufficient permissions", frappe.PermissionError)
    if filters and isinstance(filters, str):
        filters = json.loads(filters)
    base_filters = [["docstatus", "!=", 2]]
    if "Partner RM" in roles and "Finance Manager" not in roles and "Accounts Manager" not in roles:
        own_partners = frappe.get_list(
            "CRM Partner",
            filters={"partner_rm": frappe.session.user},
            pluck="name",
        )
        if not own_partners:
            return []
        base_filters.append(["partner", "in", own_partners])
    if filters:
        base_filters.extend(filters)
    return frappe.get_list(
        "CRM Partner Rebate Voucher",
        fields=["name", "partner", "deal", "customer", "payment_reference",
                "rebate_pct", "rebate_amount", "currency", "status", "creation"],
        filters=base_filters,
        limit_page_length=int(page_size),
        limit_start=int(page) * int(page_size),
        order_by="creation desc",
    )


@frappe.whitelist()
def get_sales_commissions(company=None, filters=None, page=0, page_size=20):
    roles = frappe.get_roles(frappe.session.user)
    if not (_has_ar_access(roles) or "Sales Manager" in roles):
        frappe.throw("Insufficient permissions", frappe.PermissionError)
    if filters and isinstance(filters, str):
        filters = json.loads(filters)
    base_filters = [["docstatus", "!=", 2]]
    if "Sales Manager" in roles and "Finance Manager" not in roles and "Accounts Manager" not in roles:
        own_deals = frappe.get_list(
            "CRM Deal",
            filters={"deal_owner": frappe.session.user},
            pluck="name",
        ) or ["__none__"]
        base_filters.append(["deal", "in", own_deals])
    if filters:
        base_filters.extend(filters)
    return frappe.get_list(
        "CRM Sales Commission",
        fields=["name", "sales_person", "deal", "customer", "payment_reference",
                "commission_pct", "commission_amount", "currency", "status", "creation"],
        filters=base_filters,
        limit_page_length=int(page_size),
        limit_start=int(page) * int(page_size),
        order_by="creation desc",
    )


@frappe.whitelist()
def approve_rebate_voucher(name: str, company: str = None) -> dict:
    roles = frappe.get_roles(frappe.session.user)
    if not any(r in roles for r in ("Accounts User", "Accounts Manager", "Finance Manager", "System Manager")):
        frappe.throw("Insufficient permissions", frappe.PermissionError)
    doc = frappe.get_doc("CRM Partner Rebate Voucher", name)
    doc.status = "Approved"
    doc.approved_by = frappe.session.user
    doc.approved_date = frappe.utils.nowdate()
    doc.save()
    partner_rm = frappe.db.get_value("CRM Partner", doc.partner, "partner_rm")
    if partner_rm:
        frappe.publish_realtime("crm_notification", {
            "message": "Rebate voucher %s approved" % name,
            "user": partner_rm,
        })
    _invalidate_kpi_cache(frappe.session.user, company)
    return doc.as_dict()


@frappe.whitelist()
def reject_rebate_voucher(name: str, reason: str = "", company: str = None) -> dict:
    roles = frappe.get_roles(frappe.session.user)
    if not any(r in roles for r in ("Accounts User", "Accounts Manager", "Finance Manager", "System Manager")):
        frappe.throw("Insufficient permissions", frappe.PermissionError)
    doc = frappe.get_doc("CRM Partner Rebate Voucher", name)
    doc.status = "Rejected"
    doc.rejection_reason = reason
    doc.save()
    partner_rm = frappe.db.get_value("CRM Partner", doc.partner, "partner_rm")
    if partner_rm:
        frappe.publish_realtime("crm_notification", {
            "message": "Rebate voucher %s rejected" % name,
            "user": partner_rm,
        })
    _invalidate_kpi_cache(frappe.session.user, company)
    return doc.as_dict()


@frappe.whitelist()
def mark_rebate_paid(name: str, company: str = None) -> dict:
    roles = frappe.get_roles(frappe.session.user)
    if "Finance Manager" not in roles and not _is_admin(roles):
        frappe.throw("Only Finance Manager can mark rebates as paid", frappe.PermissionError)
    doc = frappe.get_doc("CRM Partner Rebate Voucher", name)
    if doc.status != "Approved":
        frappe.throw("Rebate must be Approved before marking Paid")
    doc.status = "Paid"
    doc.paid_date = frappe.utils.nowdate()
    doc.save()
    partner_rm = frappe.db.get_value("CRM Partner", doc.partner, "partner_rm")
    if partner_rm:
        frappe.publish_realtime("crm_notification", {
            "message": "Rebate voucher %s marked as paid" % name,
            "user": partner_rm,
        })
    _invalidate_kpi_cache(frappe.session.user, company)
    return doc.as_dict()


@frappe.whitelist()
def confirm_commission(name: str, company: str = None) -> dict:
    roles = frappe.get_roles(frappe.session.user)
    if not any(r in roles for r in ("Accounts User", "Accounts Manager", "Finance Manager", "System Manager")):
        frappe.throw("Insufficient permissions", frappe.PermissionError)
    doc = frappe.get_doc("CRM Sales Commission", name)
    doc.status = "Confirmed"
    doc.confirmed_by = frappe.session.user
    doc.confirmed_date = frappe.utils.nowdate()
    doc.save()
    if doc.sales_person:
        frappe.publish_realtime("crm_notification", {
            "message": "Commission %s confirmed" % name,
            "user": doc.sales_person,
        })
    _invalidate_kpi_cache(frappe.session.user, company)
    return doc.as_dict()


@frappe.whitelist()
def reject_commission(name: str, company: str = None) -> dict:
    roles = frappe.get_roles(frappe.session.user)
    if not any(r in roles for r in ("Accounts User", "Accounts Manager", "Finance Manager", "System Manager")):
        frappe.throw("Insufficient permissions", frappe.PermissionError)
    doc = frappe.get_doc("CRM Sales Commission", name)
    doc.status = "Rejected"
    doc.save()
    if doc.sales_person:
        frappe.publish_realtime("crm_notification", {
            "message": "Commission %s rejected" % name,
            "user": doc.sales_person,
        })
    _invalidate_kpi_cache(frappe.session.user, company)
    return doc.as_dict()


@frappe.whitelist()
def mark_commission_paid(name: str, company: str = None) -> dict:
    roles = frappe.get_roles(frappe.session.user)
    if "Finance Manager" not in roles and not _is_admin(roles):
        frappe.throw("Only Finance Manager can mark commissions as paid", frappe.PermissionError)
    doc = frappe.get_doc("CRM Sales Commission", name)
    if doc.status != "Confirmed":
        frappe.throw("Commission must be Confirmed before marking Paid")
    doc.status = "Paid"
    doc.paid_date = frappe.utils.nowdate()
    doc.save()
    if doc.sales_person:
        frappe.publish_realtime("crm_notification", {
            "message": "Commission %s marked as paid" % name,
            "user": doc.sales_person,
        })
    _invalidate_kpi_cache(frappe.session.user, company)
    return doc.as_dict()


def _invalidate_kpi_cache(user, company):
    if not company:
        return
    for period in ("month", "quarter", "year", "ytd"):
        frappe.cache().delete_value("fc_kpis_%s_%s_%s" % (user, company, period))


# ---------------------------------------------------------------------------
# fc-s3-4: Banking APIs
# ---------------------------------------------------------------------------

@frappe.whitelist()
def get_bank_accounts(company=None):
    roles = frappe.get_roles(frappe.session.user)
    if not (_has_ar_access(roles) or _has_ap_access(roles)):
        frappe.throw("Insufficient permissions", frappe.PermissionError)
    company = company or frappe.defaults.get_user_default("company")
    frappe.has_permission("Company", doc=company, ptype="read", throw=True)
    if not frappe.db.exists("DocType", "Bank Account"):
        return []
    return frappe.get_list(
        "Bank Account",
        fields=["name", "bank", "account", "is_company_account"],
        filters=[["company", "=", company], ["is_company_account", "=", 1]],
        order_by="name asc",
    )


@frappe.whitelist()
def get_bank_transactions(company=None, filters=None, page=0, page_size=20):
    roles = frappe.get_roles(frappe.session.user)
    if not (_has_ar_access(roles) or _has_ap_access(roles)):
        frappe.throw("Insufficient permissions", frappe.PermissionError)
    company = company or frappe.defaults.get_user_default("company")
    frappe.has_permission("Company", doc=company, ptype="read", throw=True)
    if not frappe.db.exists("DocType", "Bank Transaction"):
        return []
    if filters and isinstance(filters, str):
        filters = json.loads(filters)
    base_filters = [["company", "=", company]]
    if filters:
        base_filters.extend(filters)
    return frappe.get_list(
        "Bank Transaction",
        fields=["name", "date", "description", "deposit", "withdrawal",
                "currency", "status", "bank_account"],
        filters=base_filters,
        limit_page_length=int(page_size),
        limit_start=int(page) * int(page_size),
        order_by="date desc",
    )


@frappe.whitelist()
def approve_purchase_invoice(name: str) -> dict:
    roles = frappe.get_roles(frappe.session.user)
    if "Finance Manager" not in roles and not _is_admin(roles):
        frappe.throw("Only Finance Manager can approve purchase invoices", frappe.PermissionError)
    doc = frappe.get_doc("Purchase Invoice", name)
    frappe.has_permission("Company", doc=doc.company, ptype="read", throw=True)
    doc.submit()
    return {"status": "submitted", "name": name}


# ---------------------------------------------------------------------------
# fc-s4-1: Dashboard charts
# ---------------------------------------------------------------------------

def _get_cashflow_series(company, months=6):
    """Return [{month, inflow, outflow}, ...] for the last N months."""
    t = date.fromisoformat(today())
    result = []
    for i in range(months - 1, -1, -1):
        # target month = today minus i months
        ref = date(t.year, t.month, 1)
        y = ref.year
        m = ref.month - i
        while m <= 0:
            m += 12
            y -= 1
        first = date(y, m, 1).isoformat()
        last_day = calendar.monthrange(y, m)[1]
        last = date(y, m, last_day).isoformat()
        label = date(y, m, 1).strftime("%b %Y")

        inflow_rows = frappe.get_list(
            "Payment Entry",
            filters=[
                ["company", "=", company],
                ["docstatus", "=", 1],
                ["payment_type", "=", "Receive"],
                ["posting_date", ">=", first],
                ["posting_date", "<=", last],
            ],
            fields=[{"SUM": "paid_amount", "as": "total"}],
            limit=1,
        )
        outflow_rows = frappe.get_list(
            "Payment Entry",
            filters=[
                ["company", "=", company],
                ["docstatus", "=", 1],
                ["payment_type", "=", "Pay"],
                ["posting_date", ">=", first],
                ["posting_date", "<=", last],
            ],
            fields=[{"SUM": "paid_amount", "as": "total"}],
            limit=1,
        )
        result.append({
            "month": label,
            "inflow": float(inflow_rows[0].total or 0) if inflow_rows else 0,
            "outflow": float(outflow_rows[0].total or 0) if outflow_rows else 0,
        })
    return result


def _get_ar_aging_buckets(company):
    today_str = today()
    rows = frappe.get_list(
        "Sales Invoice",
        filters=[
            ["company", "=", company],
            ["docstatus", "=", 1],
            ["outstanding_amount", ">", 0],
        ],
        fields=["outstanding_amount", "due_date"],
        limit=500,
    )
    buckets = {"Current": 0, "1-30d": 0, "31-60d": 0, "60+d": 0}
    for r in rows:
        age = max(0, int(date_diff(today_str, str(r.due_date)))) if r.due_date else 0
        amt = float(r.outstanding_amount or 0)
        if age <= 0:
            buckets["Current"] += amt
        elif age <= 30:
            buckets["1-30d"] += amt
        elif age <= 60:
            buckets["31-60d"] += amt
        else:
            buckets["60+d"] += amt
    return [{"bucket": k, "amount": v} for k, v in buckets.items()]


def _get_ap_aging_buckets(company):
    today_str = today()
    rows = frappe.get_list(
        "Purchase Invoice",
        filters=[
            ["company", "=", company],
            ["docstatus", "=", 1],
            ["outstanding_amount", ">", 0],
        ],
        fields=["outstanding_amount", "due_date"],
        limit=500,
    )
    buckets = {"Current": 0, "1-30d": 0, "31-60d": 0, "60+d": 0}
    for r in rows:
        age = max(0, int(date_diff(today_str, str(r.due_date)))) if r.due_date else 0
        amt = float(r.outstanding_amount or 0)
        if age <= 0:
            buckets["Current"] += amt
        elif age <= 30:
            buckets["1-30d"] += amt
        elif age <= 60:
            buckets["31-60d"] += amt
        else:
            buckets["60+d"] += amt
    return [{"bucket": k, "amount": v} for k, v in buckets.items()]


def _get_pl_summary(company, from_date, to_date):
    income_rows = frappe.get_list(
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
    expense_rows = frappe.get_list(
        "Purchase Invoice",
        filters=[
            ["company", "=", company],
            ["docstatus", "=", 1],
            ["posting_date", ">=", from_date],
            ["posting_date", "<=", to_date],
        ],
        fields=[{"SUM": "grand_total", "as": "total"}],
        limit=1,
    )
    income = float(income_rows[0].total or 0) if income_rows else 0
    expenses = float(expense_rows[0].total or 0) if expense_rows else 0
    return {
        "income": income,
        "expenses": expenses,
        "net": income - expenses,
        "period_label": "%s to %s" % (from_date, to_date),
    }


@frappe.whitelist()
def get_dashboard_charts(company=None, period="month"):
    company = company or frappe.defaults.get_user_default("company")
    frappe.has_permission("Company", doc=company, ptype="read", throw=True)
    roles = frappe.get_roles(frappe.session.user)
    if not (_has_ar_access(roles) or _has_ap_access(roles) or _is_admin(roles)):
        frappe.throw("Insufficient permissions", frappe.PermissionError)

    from_date, to_date = _get_date_filter(period)
    result = {"cashflow": _get_cashflow_series(company)}
    if _has_ar_access(roles):
        result["ar_aging"] = _get_ar_aging_buckets(company)
        result["pl"] = _get_pl_summary(company, from_date, to_date)
    if _has_ap_access(roles):
        result["ap_aging"] = _get_ap_aging_buckets(company)
    # Finance Manager gets everything
    if _is_admin(roles) or "Finance Manager" in roles:
        if "ar_aging" not in result:
            result["ar_aging"] = _get_ar_aging_buckets(company)
        if "pl" not in result:
            result["pl"] = _get_pl_summary(company, from_date, to_date)
        if "ap_aging" not in result:
            result["ap_aging"] = _get_ap_aging_buckets(company)
    return result


# ---------------------------------------------------------------------------
# fc-s4-3: General Ledger, Assets, Liabilities APIs
# ---------------------------------------------------------------------------

def _require_finance_manager():
    roles = frappe.get_roles(frappe.session.user)
    if "Finance Manager" not in roles and not _is_admin(roles):
        frappe.throw("Finance Manager role required", frappe.PermissionError)


@frappe.whitelist()
def get_journal_entries(company=None, filters=None, page=0, page_size=20):
    _require_finance_manager()
    company = company or frappe.defaults.get_user_default("company")
    frappe.has_permission("Company", doc=company, ptype="read", throw=True)
    if filters and isinstance(filters, str):
        filters = json.loads(filters)
    base_filters = [["company", "=", company], ["docstatus", "!=", 2]]
    if filters:
        base_filters.extend(filters)
    return frappe.get_list(
        "Journal Entry",
        filters=base_filters,
        fields=["name", "posting_date", "entry_type", "total_debit", "remark", "docstatus"],
        order_by="posting_date desc",
        limit_page_length=int(page_size),
        limit_start=int(page) * int(page_size),
    )


@frappe.whitelist()
def get_gl_entries(company=None, filters=None, page=0, page_size=50):
    _require_finance_manager()
    company = company or frappe.defaults.get_user_default("company")
    frappe.has_permission("Company", doc=company, ptype="read", throw=True)
    if filters and isinstance(filters, str):
        filters = json.loads(filters)
    base_filters = [["company", "=", company], ["is_cancelled", "=", 0]]
    if filters:
        base_filters.extend(filters)
    return frappe.get_list(
        "GL Entry",
        filters=base_filters,
        fields=[
            "name", "posting_date", "account", "party_type", "party",
            "debit", "credit", "voucher_type", "voucher_no",
            "cost_center", "remarks",
        ],
        order_by="posting_date desc",
        limit_page_length=int(page_size),
        limit_start=int(page) * int(page_size),
    )


@frappe.whitelist()
def get_period_closing_vouchers(company=None, page=0, page_size=20):
    _require_finance_manager()
    company = company or frappe.defaults.get_user_default("company")
    frappe.has_permission("Company", doc=company, ptype="read", throw=True)
    if not frappe.db.exists("DocType", "Period Closing Voucher"):
        return []
    return frappe.get_list(
        "Period Closing Voucher",
        filters=[["company", "=", company]],
        fields=["name", "transaction_date", "fiscal_year", "closing_account_head", "remarks"],
        order_by="transaction_date desc",
        limit_page_length=int(page_size),
        limit_start=int(page) * int(page_size),
    )


@frappe.whitelist()
def get_subscriptions(company=None, filters=None, page=0, page_size=20):
    _require_finance_manager()
    company = company or frappe.defaults.get_user_default("company")
    frappe.has_permission("Company", doc=company, ptype="read", throw=True)
    if not frappe.db.exists("DocType", "Subscription"):
        return []
    if filters and isinstance(filters, str):
        filters = json.loads(filters)
    base_filters = [["company", "=", company]]
    if filters:
        base_filters.extend(filters)
    return frappe.get_list(
        "Subscription",
        filters=base_filters,
        fields=["name", "party", "status", "current_invoice_start",
                "current_invoice_end", "days_until_due"],
        order_by="current_invoice_end asc",
        limit_page_length=int(page_size),
        limit_start=int(page) * int(page_size),
    )


@frappe.whitelist()
def get_assets(company=None, filters=None, page=0, page_size=20):
    _require_finance_manager()
    company = company or frappe.defaults.get_user_default("company")
    frappe.has_permission("Company", doc=company, ptype="read", throw=True)
    if not frappe.db.exists("DocType", "Asset"):
        return []
    if filters and isinstance(filters, str):
        filters = json.loads(filters)
    base_filters = [["company", "=", company], ["docstatus", "!=", 2]]
    if filters:
        base_filters.extend(filters)
    return frappe.get_list(
        "Asset",
        filters=base_filters,
        fields=[
            "name", "asset_name", "asset_category", "purchase_date",
            "gross_purchase_amount", "accumulated_depreciation_amount",
            "value_after_depreciation", "status",
        ],
        order_by="purchase_date desc",
        limit_page_length=int(page_size),
        limit_start=int(page) * int(page_size),
    )


@frappe.whitelist()
def get_depreciation_schedule(company=None, page=0, page_size=20):
    _require_finance_manager()
    company = company or frappe.defaults.get_user_default("company")
    frappe.has_permission("Company", doc=company, ptype="read", throw=True)
    if not frappe.db.exists("DocType", "Asset Depreciation Schedule"):
        return []
    cutoff = add_months(today(), 1)
    return frappe.get_list(
        "Asset Depreciation Schedule",
        filters=[["company", "=", company], ["schedule_date", "<=", cutoff]],
        fields=["name", "asset", "schedule_date", "depreciation_amount",
                "depreciation_method", "fiscal_year"],
        order_by="schedule_date asc",
        limit_page_length=int(page_size),
        limit_start=int(page) * int(page_size),
    )


@frappe.whitelist()
def get_asset_movements(company=None, page=0, page_size=20):
    _require_finance_manager()
    company = company or frappe.defaults.get_user_default("company")
    frappe.has_permission("Company", doc=company, ptype="read", throw=True)
    if not frappe.db.exists("DocType", "Asset Movement"):
        return []
    return frappe.get_list(
        "Asset Movement",
        filters=[["company", "=", company], ["docstatus", "!=", 2]],
        fields=["name", "transaction_date", "purpose", "company"],
        order_by="transaction_date desc",
        limit_page_length=int(page_size),
        limit_start=int(page) * int(page_size),
    )
