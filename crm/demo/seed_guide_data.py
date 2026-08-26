"""
seed_guide_data.py — Creates guide-ready Quotations at every lifecycle stage
for the Finance Module user guide screenshots.

Run via:
  bench --site cr-dev.tiberbu.app execute crm.demo.seed_guide_data.run
"""
import frappe


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────

def _existing_quote(deal, status):
    """
    Return the name of an existing Quotation for this deal at the given derived
    status ("Draft" / "Sent" / "Accepted" / "Rejected"), else None. The engine
    stores ERPNext Quotations (status derived from docstatus + crm_sent), so
    idempotency must resolve status through _derive_status — not a stored field.
    """
    from crm.api.quotes import _derive_status
    for name in frappe.get_list("Quotation", filters={"crm_deal": deal}, pluck="name"):
        if _derive_status(frappe.get_doc("Quotation", name)) == status:
            return name
    return None


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


# Package tier → ERPNext subscription / implementation Item codes
_TIER_SKUS = {
    "Core":       ("CV-HIMS-SUB-CORE", "CV-HIMS-IMPL-CORE"),
    "Advanced":   ("CV-HIMS-SUB-ADV",  "CV-HIMS-IMPL-ADV"),
    "Enterprise": ("CV-HIMS-SUB-ENT",  "CV-HIMS-IMPL-ENT"),
}


def _save_quote(deal, facilities, addons, payment_terms="Annual Upfront",
                contract_term_yrs=3, notes=None):
    """
    Seed a Quotation via the line-item quote engine. Rates are omitted so
    save_quote_lines defaults each line from the quote's Item Price.
    Returns the doc name.
    """
    import json
    from crm.api.quotes import create_quote, save_quote_lines

    name = create_quote(deal)["name"]

    lines = []
    for f in facilities:
        sub_sku, impl_sku = _TIER_SKUS.get(f.get("package_tier"), _TIER_SKUS["Core"])
        fname = f.get("facility_name", "")
        lines.append({
            "item_code": sub_sku, "qty": 1,
            "item_name": f"Careverse HMIS Subscription — {fname}",
            "facility_name": fname, "package_tier": f.get("package_tier", ""),
        })
        lines.append({
            "item_code": impl_sku, "qty": 1,
            "item_name": f"Careverse HMIS Implementation — {fname}",
            "facility_name": fname, "package_tier": f.get("package_tier", ""),
        })
    for a in addons:
        if (a.get("qty") or 0) > 0:
            lines.append({
                "item_code": a.get("product_sku"), "qty": a.get("qty"),
            })

    save_quote_lines(name, json.dumps(lines))
    if notes:
        frappe.db.set_value("Quotation", name, "terms", notes)
        frappe.db.commit()
    return name


def _mark_sent(quote_name):
    from crm.api.quotes import send_quote
    send_quote(quote_name)


def _mark_accepted(quote_name):
    from crm.api.quotes import accept_quote
    return accept_quote(quote_name).get("invoice_name", "")


def _mark_rejected(quote_name):
    from crm.api.quotes import reject_quote
    reject_quote(quote_name)


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
        existing = _existing_quote(deal_knh, "Draft")
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
            results["draft_knh"] = existing
            print("DRAFT quote already exists for KNH: %s" % existing)

    # ── 2. SENT quote — Mater Hospital ───────────────────────────────────
    deal_mater = deals_by_org.get("Mater Hospital") or org_to_deal.get("Mater Hospital")
    if deal_mater:
        existing_sent = _existing_quote(deal_mater, "Sent")
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
            results["sent_mater"] = existing_sent
            print("SENT quote already exists for Mater: %s" % existing_sent)

    # ── 3. ACCEPTED quote → Sales Invoice — Kisumu County ────────────────
    deal_kisumu = deals_by_org.get("Kisumu County Referral Hospital") or org_to_deal.get(
        "Kisumu County Referral Hospital"
    )
    if deal_kisumu:
        existing_accepted = _existing_quote(deal_kisumu, "Accepted")
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
            from crm.api.quotes import _invoice_for_quotation
            results["accepted_kisumu"] = existing_accepted
            results["invoice_kisumu"] = _invoice_for_quotation(existing_accepted)
            print("ACCEPTED quote already exists for Kisumu: %s" % existing_accepted)

    # ── 4. MULTI-FACILITY ACCEPTED quote — Aga Khan ───────────────────────
    deal_aga = deals_by_org.get("Aga Khan University Hospital") or org_to_deal.get(
        "Aga Khan University Hospital"
    )
    if deal_aga:
        existing_multi = _existing_quote(deal_aga, "Accepted")
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
            results["accepted_aga_khan"] = existing_multi
            print("ACCEPTED quote already exists for Aga Khan: %s" % existing_multi)

    # ── 5. SENT (awaiting acceptance) — Nairobi Women's Hospital ─────────
    deal_nwh = deals_by_org.get("Nairobi Women's Hospital") or org_to_deal.get(
        "Nairobi Women's Hospital"
    )
    if deal_nwh:
        existing_nwh = _existing_quote(deal_nwh, "Sent")
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
            results["sent_nwh"] = existing_nwh
            print("SENT quote already exists for NWH: %s" % existing_nwh)

    print("\n=== Seed complete ===")
    for k, v in results.items():
        print("  %-30s %s" % (k, v))
    return results
