"""
crm/patches/v1_0/seed_catalogue_items.py

Provision the CareVerse Quote-Builder / Finance-Cockpit product catalogue in
ERPNext so quote -> Sales Invoice conversion resolves real Item links.

Background
----------
The 15 CRM Products (product_code CV-*) ship as a fixture
(crm/fixtures/crm_product_catalogue.json) and carry an ``erpnext_item_code``
that points at the matching ERPNext Item. Nothing, however, created those
Items on a fresh site -- they only ever existed on dev because the manual
demo helper ``crm.demo.seed_erpnext_items.run()`` was executed by hand. On a
clean production migrate the CRM Product links dangled, and
crm.api.quotes / invoice_adapter (which require ``frappe.db.exists("Item", ...)``)
fell back to the raw SKU string, breaking Sales Invoice creation.

This patch promotes that demo data into a wired, idempotent migration.

Source of truth for the codes/names/rates:
  - crm/demo/seed_erpnext_items.py  (SKU master)
  - crm/fixtures/crm_product_catalogue.json  (standard_rate — matches below)

Idempotent: every insert is guarded by an existence check. Safe to re-run.
"""
from __future__ import annotations

import frappe

PRICE_LIST = "Standard Selling"

# (name, parent) — parents are ERPNext default Item Groups.
ITEM_GROUPS = [
    ("CareVerse HMIS", "Products"),
    ("CareVerse Hardware", "Products"),
    ("CareVerse Services", "Services"),
]

# (item_code, item_name, item_group, rate_kes) — verbatim from the SKU master.
SKUS = [
    ("CV-HIMS-SUB-CORE",         "Careverse HMIS Subscription — Core",                    "CareVerse HMIS",      605149.06),
    ("CV-HIMS-SUB-ADV",          "Careverse HMIS Subscription — Advanced",                "CareVerse HMIS",     1821349.83),
    ("CV-HIMS-SUB-ENT",          "Careverse HMIS Subscription — Enterprise",              "CareVerse HMIS",     6044783.95),
    ("CV-HIMS-IMPL-CORE",        "Careverse HMIS Implementation & Training — Core",       "CareVerse HMIS",      620000.00),
    ("CV-HIMS-IMPL-ADV",         "Careverse HMIS Implementation & Training — Advanced",   "CareVerse HMIS",     1870000.00),
    ("CV-HIMS-IMPL-ENT",         "Careverse HMIS Implementation & Training — Enterprise", "CareVerse HMIS",     6180000.00),
    ("CV-HW-OPTIPLEX-7010",      "Endpoint Workstation — Dell OptiPlex 7010 MT",          "CareVerse Hardware",   84000.00),
    ("CV-HW-LATITUDE-5440",      "Endpoint Laptop — Dell Latitude 5440",                  "CareVerse Hardware",  126000.00),
    ("CV-HW-TAB-10",             "Endpoint Tablet — 10.1\" Android",                      "CareVerse Hardware",   38888.89),
    ("CV-SW-ENDPOINT-SEC",       "Endpoint Security Subscription",                        "CareVerse HMIS",        8100.00),
    ("CV-SW-OFFICE-MGMT",        "Office Management Suite",                               "CareVerse HMIS",       13885.71),
    ("CV-SVC-OUT-NAIROBI",       "Implementation Outside Nairobi",                        "CareVerse Services",   14500.00),
    ("CV-SVC-REFRESHER-VIRT",    "Refresher Training — Virtual",                          "CareVerse Services",    2500.00),
    ("CV-SVC-ONSITE-ENGINEER",   "On-Site Support Engineer (5 days/wk)",                  "CareVerse Services",  220000.00),
    ("CV-SVC-PARTTIME-ENGINEER", "Part-Time Support Engineer (2 days/wk)",                "CareVerse Services",  100000.00),
]


def execute():
    # ERPNext owns Item / Item Group / Item Price / Price List. If it is not
    # installed this catalogue is not applicable — skip cleanly.
    if "erpnext" not in frappe.get_installed_apps():
        return

    _seed_item_groups()
    _seed_items()
    _seed_item_prices()
    frappe.db.commit()


def _seed_item_groups():
    for group_name, parent in ITEM_GROUPS:
        if frappe.db.exists("Item Group", group_name):
            continue
        frappe.get_doc({
            "doctype": "Item Group",
            "item_group_name": group_name,
            "parent_item_group": parent,
        }).insert(ignore_permissions=True)  # SYSTEM-INTERNAL


def _seed_items():
    for item_code, item_name, item_group, _rate in SKUS:
        if frappe.db.exists("Item", item_code):
            continue
        doc = frappe.get_doc({
            "doctype": "Item",
            "item_code": item_code,
            "item_name": item_name,
            "item_group": item_group,
            "stock_uom": "Nos",
            "is_sales_item": 1,
            "is_stock_item": 0,
            "include_item_in_manufacturing": 0,
            "description": item_name,
        })
        # Do not let the Item->CRM Product sync hook fire during migration:
        # the CRM Products ship as a fixture and already own the link.
        doc.flags.ignore_crm_sync = True
        doc.insert(ignore_permissions=True)  # SYSTEM-INTERNAL


def _seed_item_prices():
    if not frappe.db.exists("Price List", PRICE_LIST):
        # "Standard Selling" is an ERPNext default; only create as a fallback.
        frappe.get_doc({
            "doctype": "Price List",
            "price_list_name": PRICE_LIST,
            "currency": "KES",
            "selling": 1,
            "enabled": 1,
        }).insert(ignore_permissions=True)  # SYSTEM-INTERNAL

    for item_code, _item_name, _item_group, rate in SKUS:
        if frappe.db.exists("Item Price", {"item_code": item_code, "price_list": PRICE_LIST}):
            continue
        frappe.get_doc({
            "doctype": "Item Price",
            "item_code": item_code,
            "price_list": PRICE_LIST,
            "price_list_rate": rate,
            "currency": "KES",
            "uom": "Nos",
        }).insert(ignore_permissions=True)  # SYSTEM-INTERNAL
