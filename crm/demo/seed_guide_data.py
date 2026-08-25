"""
seed_guide_data.py — Creates guide-ready CRM Quotes at every lifecycle stage
for the Finance Module user guide screenshots.

Run via:
  bench --site cr-dev.tiberbu.app execute crm.demo.seed_guide_data.run
"""
import frappe
from frappe.utils import nowdate, add_days


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────

def _find_deal_with_org(org_name):
    """Return the name of a deal whose organization matches org_name."""
    deals = frappe.get_list("CRM Deal", filters={"organization": org_name}, pluck="name", limit=1)
    return deals[0] if deals else None


def _find_any_deal():
    """Return any deal name available on site."""
    deals = frappe.get_list("CRM Deal", fields=["name", "organization"], limit=5)
    # Prefer deals with a real org name
    for d in deals:
        if d.organization:
            return d.name, d.organization
    return deals[0].name, None if deals else (None, None)


def _save_quote(deal, facilities, addons, payment_terms="Annual Upfront",
                contract_term_yrs=3, notes=None):
    """Save a quote via the internal API, returns the doc name."""
    import json
    from crm.api.quotes import save_quote

    quote_data = {
        "deal": deal,
        "quote_date": nowdate(),
        "valid_until": add_days(nowdate(), 30),
        "contract_start_date": add_days(nowdate(), 14),
        "payment_terms": payment_terms,
        "contract_term_yrs": contract_term_yrs,
        "currency": "KES",
        "facilities": facilities,
        "addons": addons,
        "notes": notes or "",
    }
    result = save_quote(json.dumps(quote_data))
    return result["name"]


def _mark_sent(quote_name):
    frappe.db.set_value("CRM Quote", quote_name, "status", "Sent")
    frappe.db.set_value("CRM Quote", quote_name, "submitted_by", frappe.session.user)
    frappe.db.commit()


def _mark_accepted(quote_name):
    from crm.integrations.erpnext.invoice_adapter import create_sales_invoice
    doc = frappe.get_doc("CRM Quote", quote_name)
    result = create_sales_invoice(doc)
    invoice_name = result.get("invoice_name", "")
    frappe.db.set_value("CRM Quote", quote_name, "status", "Accepted")
    if invoice_name:
        frappe.db.set_value("CRM Quote", quote_name, "erpnext_sales_invoice", invoice_name)
    frappe.db.commit()
    return invoice_name


def _mark_rejected(quote_name):
    frappe.db.set_value("CRM Quote", quote_name, "status", "Rejected")
    frappe.db.commit()


# ──────────────────────────────────────────────
# Facility definitions (realistic Kenyan hospitals)
# ──────────────────────────────────────────────

KNH_ADVANCED_FACILITIES = [
    {
        "facility_name": "Kenyatta National Hospital — Main Campus",
        "package_tier": "Advanced",
        "num_users": 250,
        "subscription_discount": 10.0,
        "impl_discount": 20.0,
    },
    {
        "facility_name": "KNH Annex — Paediatric Unit",
        "package_tier": "Core",
        "num_users": 60,
        "subscription_discount": 10.0,
        "impl_discount": 20.0,
    },
]

MATER_ENTERPRISE_FACILITIES = [
    {
        "facility_name": "Mater Hospital Nairobi",
        "package_tier": "Enterprise",
        "num_users": 400,
        "subscription_discount": 15.0,
        "impl_discount": 30.0,
    },
]

KISUMU_CORE_FACILITIES = [
    {
        "facility_name": "Kisumu County Referral Hospital",
        "package_tier": "Core",
        "num_users": 120,
        "subscription_discount": 5.0,
        "impl_discount": 15.0,
    },
]

AGA_KHAN_ENTERPRISE_FACILITIES = [
    {
        "facility_name": "Aga Khan University Hospital — Nairobi",
        "package_tier": "Enterprise",
        "num_users": 500,
        "subscription_discount": 20.0,
        "impl_discount": 35.0,
    },
    {
        "facility_name": "Aga Khan Hospital — Mombasa",
        "package_tier": "Advanced",
        "num_users": 180,
        "subscription_discount": 20.0,
        "impl_discount": 35.0,
    },
]

NAIROBI_WOMENS_FACILITIES = [
    {
        "facility_name": "Nairobi Women's Hospital — Hurlingham",
        "package_tier": "Advanced",
        "num_users": 150,
        "subscription_discount": 12.0,
        "impl_discount": 25.0,
    },
    {
        "facility_name": "Nairobi Women's Hospital — Karen",
        "package_tier": "Core",
        "num_users": 80,
        "subscription_discount": 12.0,
        "impl_discount": 25.0,
    },
]

# Add-ons
TABLET_ADDON = [
    {
        "product_sku": "CV-HW-TAB-10",
        "qty": 20,
    }
]

LAPTOP_ADDON = [
    {
        "product_sku": "CV-HW-LATITUDE-5440",
        "qty": 5,
    }
]

WORKSTATION_ADDON = [
    {
        "product_sku": "CV-HW-OPTIPLEX-7010",
        "qty": 10,
    }
]


# ──────────────────────────────────────────────
# Main seed function
# ──────────────────────────────────────────────

def run():
    """
    Seed guide-ready quotes at all lifecycle stages using existing deals.
    Idempotent — skips deals that already have guide-seed quotes.
    """
    frappe.flags.in_test = True

    deals_by_org = {
        "Kenyatta National Hospital": None,
        "Mater Hospital": None,
        "Kisumu County Referral Hospital": None,
        "Aga Khan University Hospital": None,
        "Nairobi Women's Hospital": None,
    }

    # Find deals for each org
    for org in list(deals_by_org.keys()):
        deal = _find_deal_with_org(org)
        if deal:
            deals_by_org[org] = deal

    # Map fallbacks: if specific org deals not found, use any existing deal
    available_deals = frappe.get_list(
        "CRM Deal",
        filters=[["organization", "!=", ""], ["organization", "is", "set"]],
        fields=["name", "organization"],
        limit=20,
    )
    org_to_deal = {d.organization: d.name for d in available_deals if d.organization}

    results = {}

    # ── 1. DRAFT quote — Kenyatta National Hospital ──────────────────────
    deal_knh = deals_by_org.get("Kenyatta National Hospital") or org_to_deal.get(
        "Kenyatta National Hospital"
    )
    if deal_knh:
        existing = frappe.get_list(
            "CRM Quote",
            filters={"deal": deal_knh, "status": "Draft"},
            pluck="name",
            limit=1,
        )
        if not existing:
            name = _save_quote(
                deal=deal_knh,
                facilities=KNH_ADVANCED_FACILITIES,
                addons=LAPTOP_ADDON,
                payment_terms="Annual Upfront",
                contract_term_yrs=3,
                notes=(
                    "Proposed Advanced tier for main campus with Core tier for the Paediatric annex. "
                    "3-year contract, annual billing. Subject to board approval."
                ),
            )
            results["draft_knh"] = name
            print("Created DRAFT quote %s for Kenyatta National Hospital" % name)
        else:
            results["draft_knh"] = existing[0]
            print("DRAFT quote already exists for KNH: %s" % existing[0])

    # ── 2. SENT quote — Mater Hospital ───────────────────────────────────
    deal_mater = deals_by_org.get("Mater Hospital") or org_to_deal.get("Mater Hospital")
    if deal_mater:
        existing_sent = frappe.get_list(
            "CRM Quote",
            filters={"deal": deal_mater, "status": "Sent"},
            pluck="name",
            limit=1,
        )
        if not existing_sent:
            name = _save_quote(
                deal=deal_mater,
                facilities=MATER_ENTERPRISE_FACILITIES,
                addons=WORKSTATION_ADDON,
                payment_terms="Quarterly Advance",
                contract_term_yrs=5,
                notes=(
                    "Enterprise tier for the full hospital network. Quarterly advance payment. "
                    "Implementation to begin Q3 2026."
                ),
            )
            _mark_sent(name)
            results["sent_mater"] = name
            print("Created SENT quote %s for Mater Hospital" % name)
        else:
            results["sent_mater"] = existing_sent[0]
            print("SENT quote already exists for Mater: %s" % existing_sent[0])

    # ── 3. ACCEPTED quote → Sales Invoice — Kisumu County ────────────────
    deal_kisumu = deals_by_org.get("Kisumu County Referral Hospital") or org_to_deal.get(
        "Kisumu County Referral Hospital"
    )
    if deal_kisumu:
        existing_accepted = frappe.get_list(
            "CRM Quote",
            filters={"deal": deal_kisumu, "status": "Accepted"},
            pluck="name",
            limit=1,
        )
        if not existing_accepted:
            name = _save_quote(
                deal=deal_kisumu,
                facilities=KISUMU_CORE_FACILITIES,
                addons=TABLET_ADDON,
                payment_terms="Annual Upfront",
                contract_term_yrs=2,
                notes=(
                    "Core tier for county hospital. Includes 20 Android tablets for ward rounds. "
                    "Annual upfront payment agreed with county treasury."
                ),
            )
            _mark_sent(name)
            invoice = _mark_accepted(name)
            results["accepted_kisumu"] = name
            results["invoice_kisumu"] = invoice
            print("Created ACCEPTED quote %s → Invoice %s for Kisumu County" % (name, invoice))
        else:
            results["accepted_kisumu"] = existing_accepted[0]
            inv = frappe.db.get_value("CRM Quote", existing_accepted[0], "erpnext_sales_invoice")
            results["invoice_kisumu"] = inv
            print("ACCEPTED quote already exists for Kisumu: %s" % existing_accepted[0])

    # ── 4. MULTI-FACILITY ACCEPTED quote — Aga Khan ───────────────────────
    deal_aga = deals_by_org.get("Aga Khan University Hospital") or org_to_deal.get(
        "Aga Khan University Hospital"
    )
    if deal_aga:
        existing_multi = frappe.get_list(
            "CRM Quote",
            filters={"deal": deal_aga, "status": "Accepted"},
            pluck="name",
            limit=1,
        )
        if not existing_multi:
            name = _save_quote(
                deal=deal_aga,
                facilities=AGA_KHAN_ENTERPRISE_FACILITIES,
                addons=WORKSTATION_ADDON + TABLET_ADDON,
                payment_terms="Annual Upfront",
                contract_term_yrs=5,
                notes=(
                    "Enterprise network deal covering Nairobi flagship and Mombasa branch. "
                    "Hardware bundle included. 5-year strategic partnership."
                ),
            )
            _mark_sent(name)
            invoice = _mark_accepted(name)
            results["accepted_aga_khan"] = name
            results["invoice_aga_khan"] = invoice
            print("Created ACCEPTED multi-facility quote %s for Aga Khan" % name)
        else:
            results["accepted_aga_khan"] = existing_multi[0]
            print("ACCEPTED quote already exists for Aga Khan: %s" % existing_multi[0])

    # ── 5. SENT (awaiting acceptance) — Nairobi Women's Hospital ─────────
    deal_nwh = deals_by_org.get("Nairobi Women's Hospital") or org_to_deal.get(
        "Nairobi Women's Hospital"
    )
    if deal_nwh:
        existing_nwh = frappe.get_list(
            "CRM Quote",
            filters={"deal": deal_nwh, "status": "Sent"},
            pluck="name",
            limit=1,
        )
        if not existing_nwh:
            name = _save_quote(
                deal=deal_nwh,
                facilities=NAIROBI_WOMENS_FACILITIES,
                addons=LAPTOP_ADDON,
                payment_terms="Monthly",
                contract_term_yrs=3,
                notes=(
                    "Two-site deal — Hurlingham Advanced and Karen Core. Monthly billing requested "
                    "by their finance controller. Awaiting board sign-off."
                ),
            )
            _mark_sent(name)
            results["sent_nwh"] = name
            print("Created SENT quote %s for Nairobi Women's Hospital" % name)
        else:
            results["sent_nwh"] = existing_nwh[0]
            print("SENT quote already exists for NWH: %s" % existing_nwh[0])

    print("\n=== Seed complete ===")
    for k, v in results.items():
        print("  %-30s %s" % (k, v))
    return results
