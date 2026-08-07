import frappe
from frappe.utils import flt


# SYSTEM-INTERNAL — runs as Payment Entry on_submit; uses ignore_permissions
def on_payment_entry_submit(doc, method):
    """Auto-create Rebate Voucher and Sales Commission on Payment Entry submit."""
    if doc.payment_type != "Receive":
        return
    for ref in doc.get("references", []):
        if ref.reference_doctype != "Sales Invoice":
            continue
        try:
            invoice = frappe.get_doc("Sales Invoice", ref.reference_name)
        except frappe.DoesNotExistError:
            continue
        # Resolve CRM Deal via Customer.crm_deal custom field (set by erpnext_crm_settings integration)
        crm_deal = frappe.db.get_value("Customer", invoice.customer, "crm_deal") if invoice.customer else None
        if not crm_deal:
            continue
        _maybe_create_rebate_voucher(doc, invoice, ref, crm_deal)
        _maybe_create_commission(doc, invoice, ref, crm_deal)


def _maybe_create_rebate_voucher(payment_doc, invoice, ref, crm_deal):
    """Create a CRM Partner Rebate Voucher if the deal's lead has a partner with a rebate structure."""
    # Idempotency: skip if a voucher already exists for this payment + deal
    if frappe.db.exists("CRM Partner Rebate Voucher", {
        "payment_reference": payment_doc.name,
        "deal": crm_deal,
    }):
        return

    deal_lead = frappe.db.get_value("CRM Deal", crm_deal, "lead")
    if not deal_lead:
        return
    partner = frappe.db.get_value("CRM Lead", deal_lead, "partner")
    if not partner:
        return
    rebate_structure = frappe.db.get_value("CRM Partner", partner, "rebate_structure")
    if not rebate_structure:
        return
    rebate_pct = frappe.db.get_value("CRM Rebate Structure", rebate_structure, "rebate_pct")
    if not rebate_pct:
        return
    allocated = flt(ref.allocated_amount)
    if allocated <= 0:
        return
    rebate_amount = allocated * (rebate_pct / 100.0)

    frappe.get_doc({
        "doctype": "CRM Partner Rebate Voucher",
        "partner": partner,
        "deal": crm_deal,
        "customer": invoice.customer,
        "payment_reference": payment_doc.name,
        "rebate_structure": rebate_structure,
        "rebate_pct": rebate_pct,
        "rebate_amount": rebate_amount,
        "currency": payment_doc.paid_to_account_currency,
        "status": "Pending",
    }).insert(ignore_permissions=True)  # SYSTEM-INTERNAL


def _maybe_create_commission(payment_doc, invoice, ref, crm_deal):
    """Create a CRM Sales Commission if the deal has commission_pct set."""
    # Idempotency: skip if a commission already exists for this payment + deal
    if frappe.db.exists("CRM Sales Commission", {
        "payment_reference": payment_doc.name,
        "deal": crm_deal,
    }):
        return

    deal_vals = frappe.db.get_value(
        "CRM Deal", crm_deal, ["deal_owner", "commission_pct"], as_dict=True
    )
    if not deal_vals:
        return
    sales_person = deal_vals.deal_owner
    commission_pct = flt(deal_vals.commission_pct)
    if not sales_person or commission_pct <= 0:
        return
    allocated = flt(ref.allocated_amount)
    if allocated <= 0:
        return
    commission_amount = allocated * (commission_pct / 100.0)

    frappe.get_doc({
        "doctype": "CRM Sales Commission",
        "sales_person": sales_person,
        "deal": crm_deal,
        "customer": invoice.customer,
        "payment_reference": payment_doc.name,
        "commission_pct": commission_pct,
        "commission_amount": commission_amount,
        "currency": payment_doc.paid_to_account_currency,
        "status": "Reported",
    }).insert(ignore_permissions=True)  # SYSTEM-INTERNAL
