# CareVerse CRM — Production Deployment Setup

What a fresh production site gets **automatically** on `bench --site <site> migrate`,
and what an administrator must **still configure by hand** (tenant-specific data
that cannot be shipped in code).

> Prerequisite: **ERPNext must be installed on the site.** The catalogue/pricing
> patches skip cleanly when ERPNext is absent, but the quote → Sales Invoice and
> Finance Cockpit flows require ERPNext's `Item`, `Price List`, and
> `Sales Invoice` DocTypes.

---

## 1. Auto-provisioned — no action required

All of the following are created idempotently on every `bench migrate`.

| Provisioner | What it creates |
|---|---|
| `crm.patches.v1_0.seed_negotiated_price_lists` | 7 KEPH subscription Items (`CV-HIMS-KEPH-2 … -5`), the 5 `Negotiated Year 1–5` selling price lists, and their Item Prices (KES). Drives **opt-in portal** pricing. |
| `crm.patches.v1_0.seed_catalogue_items` | 3 Item Groups (`CareVerse HMIS/Hardware/Services`), the 15 quote-builder Items (`CV-HIMS-SUB-*`, `CV-HIMS-IMPL-*`, `CV-HW-*`, `CV-SW-*`, `CV-SVC-*`), and their `Standard Selling` Item Prices. Backs the **Quote Builder / Finance Cockpit** catalogue. |
| `crm.patches.v1_0.seed_network_coordinator_role` | `Network Coordinator` role + `User.assigned_network` custom field. |
| `crm.patches.v1_0.add_optin_crm_lead_fields` | 10 opt-in columns on `CRM Lead` (`optin_*`, `tc_*`). |
| `crm.patches.v1_0.add_quotation_crm_fields` | CareVerse custom fields on `Quotation` / `Quotation Item`; migrates `Sales Invoice.crm_quote` → `crm_quotation`. |
| `crm.setup.optin.ensure_signing_key` (after_migrate) | HMAC signing key on `CRM Opt-In Settings` (used for OTP / signing tokens). |
| `crm.setup.optin.ensure_default_terms` (after_migrate) | Default `Terms and Conditions` document, wired to `CRM Opt-In Settings.active_tc_document`. Respects an admin-chosen custom T&C. |
| `crm.setup.optin.ensure_lead_source` (after_migrate) | `Self Opt-In Portal` CRM Lead Source. |
| Fixtures (`crm/fixtures/*.json`) | 15 `CRM Product` records (`CV-*`, each linked to its ERPNext Item via `erpnext_item_code`), `Partner RM` role, `CRM Lead Approval` workflow, and the `CRM Quote Standard` / `CRM Contract Standard` print formats. |

### Verify (bench console)

```python
import frappe
assert frappe.db.count("Item", {"item_code": ["like", "CV-HIMS-KEPH-%"]}) == 7
assert frappe.db.count("Item", {"item_code": ["in", [
    "CV-HIMS-SUB-CORE","CV-HIMS-SUB-ADV","CV-HIMS-SUB-ENT",
    "CV-HIMS-IMPL-CORE","CV-HIMS-IMPL-ADV","CV-HIMS-IMPL-ENT",
    "CV-HW-OPTIPLEX-7010","CV-HW-LATITUDE-5440","CV-HW-TAB-10",
    "CV-SW-ENDPOINT-SEC","CV-SW-OFFICE-MGMT","CV-SVC-OUT-NAIROBI",
    "CV-SVC-REFRESHER-VIRT","CV-SVC-ONSITE-ENGINEER","CV-SVC-PARTTIME-ENGINEER"]]}) == 15
assert frappe.db.count("CRM Product", {"product_code": ["like", "CV-%"]}) == 15
assert frappe.db.exists("Role", "Network Coordinator")
assert frappe.get_single("CRM Opt-In Settings").active_tc_document
```

---

## 2. Manual setup required (tenant-specific — NOT auto-seeded)

These carry real business data (contacts, facility registries, mail credentials)
that must not be invented in code. Configure via the Desk UI or a bootstrap
script written for the tenant.

### 2.1 Opt-In Networks — `CRM Opt-In Network`
One record per participating association / hospital group. **Each needs a real
coordinator `contact_email`** (the OTP for every facility in that network is
routed there). Fields: `slug`, `display_name`, `enabled`, `contact_email`,
`footer_legal_name`, `price_list_override` (optional — defaults to the settings
default price list).

### 2.2 Pre-Qualified Facilities — `CRM Pre-Qualified Facility`
The registry of facilities allowed to opt in, one row per facility. Fields:
`network` (slug), `mfl_code`, `facility_name`, `keph_level` (must be one of
`Level 2 / 3 / 3A / 3B / 4 / 4B / 5` to resolve a price), `status` (`Active`),
`contact_name`, `contact_email`, `contact_phone`.

### 2.3 Outgoing Email Account (OTP delivery)
The opt-in / contract-signing OTP is sent with `frappe.sendmail()`, which needs a
default **outgoing Email Account** configured for the site. Without it, OTP
requests fail.

### 2.4 ERPNext configuration
- **Selling Settings → default selling price list** — the CRM Product ↔ Item
  sync reads `Selling Settings.selling_price_list` for catalogue rates.
- **ERPNext CRM Settings** — enable if you want two-way Item ↔ CRM Product sync
  (`should_sync()` gate). Optional; the catalogue patch does not require it.
- Confirm the site **company** and its default currency support KES pricing.

### 2.5 Confirm `CRM Opt-In Settings`
- `default_price_list` — defaults to `Negotiated Year 1`; change if a different
  negotiated year is current.
- `active_tc_document` — auto-set to the shipped default; point at a
  tenant-specific `Terms and Conditions` document if required.

---

## 3. NOT for production (development / test helpers)

Do **not** run these on a production site — they seed test data (facilities and
networks registered against a personal test inbox):

- `crm/demo/*` (all demo seeders, incl. `seed_erpnext_items.py`, `seed_guide_data.py`)
- `crm.setup.optin.ensure_optin_networks` / `seed_private_facilities` / `seed_test_facilities`

The production equivalents of the item/price data these create are shipped by the
wired patches in section 1.
