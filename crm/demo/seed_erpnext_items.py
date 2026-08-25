"""
Seed script: Create CareVerse ERPNext Item records + Item Prices on Standard Selling,
then link each back to the matching CRM Product via erpnext_item_code.

Idempotent — safe to run multiple times.

Usage (bench console):
    import importlib, crm.demo.seed_erpnext_items as m; importlib.reload(m); m.run()
"""

import frappe

# ---------------------------------------------------------------------------
# SKU master — (item_code, item_name, item_group, rate_kes)
# ---------------------------------------------------------------------------
SKUS = [
    ("CV-HIMS-SUB-CORE",         "Careverse HMIS Subscription — Core",                        "CareVerse HMIS",     605149.06),
    ("CV-HIMS-SUB-ADV",          "Careverse HMIS Subscription — Advanced",                     "CareVerse HMIS",    1821349.83),
    ("CV-HIMS-SUB-ENT",          "Careverse HMIS Subscription — Enterprise",                   "CareVerse HMIS",    6044783.95),
    ("CV-HIMS-IMPL-CORE",        "Careverse HMIS Implementation & Training — Core",             "CareVerse HMIS",     620000.00),
    ("CV-HIMS-IMPL-ADV",         "Careverse HMIS Implementation & Training — Advanced",         "CareVerse HMIS",    1870000.00),
    ("CV-HIMS-IMPL-ENT",         "Careverse HMIS Implementation & Training — Enterprise",       "CareVerse HMIS",    6180000.00),
    ("CV-HW-OPTIPLEX-7010",      "Endpoint Workstation — Dell OptiPlex 7010 MT",               "CareVerse Hardware",  84000.00),
    ("CV-HW-LATITUDE-5440",      "Endpoint Laptop — Dell Latitude 5440",                       "CareVerse Hardware", 126000.00),
    ("CV-HW-TAB-10",             "Endpoint Tablet — 10.1\" Android",                           "CareVerse Hardware",  38888.89),
    ("CV-SW-ENDPOINT-SEC",       "Endpoint Security Subscription",                             "CareVerse HMIS",      8100.00),
    ("CV-SW-OFFICE-MGMT",        "Office Management Suite",                                    "CareVerse HMIS",     13885.71),
    ("CV-SVC-OUT-NAIROBI",       "Implementation Outside Nairobi",                             "CareVerse Services",  14500.00),
    ("CV-SVC-REFRESHER-VIRT",    "Refresher Training — Virtual",                               "CareVerse Services",  2500.00),
    ("CV-SVC-ONSITE-ENGINEER",   "On-Site Support Engineer (5 days/wk)",                       "CareVerse Services", 220000.00),
    ("CV-SVC-PARTTIME-ENGINEER", "Part-Time Support Engineer (2 days/wk)",                     "CareVerse Services", 100000.00),
]

# Item Group definitions: (name, parent)
ITEM_GROUPS = [
    ("CareVerse HMIS",     "Products"),
    ("CareVerse Hardware", "Products"),
    ("CareVerse Services", "Services"),
]

PRICE_LIST = "Standard Selling"


def _ensure_item_group(group_name: str, parent: str) -> None:
    if frappe.db.exists("Item Group", group_name):
        return
    doc = frappe.new_doc("Item Group")
    doc.item_group_name = group_name
    doc.parent_item_group = parent
    doc.insert(ignore_permissions=True)  # SYSTEM-INTERNAL
    frappe.db.commit()
    print(f"  Created Item Group: {group_name} (under {parent})")


def _ensure_item(item_code: str, item_name: str, item_group: str) -> None:
    if frappe.db.exists("Item", item_code):
        print(f"  SKIP Item {item_code} — already exists")
        return
    doc = frappe.new_doc("Item")
    doc.item_code = item_code
    doc.item_name = item_name
    doc.item_group = item_group
    doc.is_sales_item = 1
    doc.is_stock_item = 0
    doc.include_item_in_manufacturing = 0
    doc.description = item_name
    doc.insert(ignore_permissions=True)  # SYSTEM-INTERNAL
    frappe.db.commit()
    print(f"  Created Item: {item_code}")


def _ensure_item_price(item_code: str, rate: float) -> None:
    existing = frappe.db.get_value(
        "Item Price",
        {"item_code": item_code, "price_list": PRICE_LIST},
        "name",
    )
    if existing:
        print(f"  SKIP Item Price {item_code} — already exists ({existing})")
        return
    doc = frappe.new_doc("Item Price")
    doc.item_code = item_code
    doc.price_list = PRICE_LIST
    doc.price_list_rate = rate
    doc.currency = "KES"
    doc.insert(ignore_permissions=True)  # SYSTEM-INTERNAL
    frappe.db.commit()
    print(f"  Created Item Price: {item_code} @ KES {rate:,.2f}")


def _link_crm_product(product_code: str, item_code: str) -> None:
    if not frappe.db.exists("CRM Product", product_code):
        print(f"  WARN CRM Product {product_code} not found — skipping link")
        return
    current = frappe.db.get_value("CRM Product", product_code, "erpnext_item_code")
    if current == item_code:
        print(f"  SKIP CRM Product {product_code} link — already set")
        return
    frappe.db.set_value(
        "CRM Product",
        product_code,
        "erpnext_item_code",
        item_code,
        update_modified=False,
    )
    frappe.db.commit()
    print(f"  Linked CRM Product {product_code} -> {item_code}")


def run() -> None:
    print("\n=== CareVerse Item Seed ===")

    print("\n-- Item Groups --")
    for group_name, parent in ITEM_GROUPS:
        _ensure_item_group(group_name, parent)

    print("\n-- Items --")
    for item_code, item_name, item_group, _rate in SKUS:
        _ensure_item(item_code, item_name, item_group)

    print("\n-- Item Prices --")
    for item_code, _item_name, _item_group, rate in SKUS:
        _ensure_item_price(item_code, rate)

    print("\n-- CRM Product links --")
    for item_code, _item_name, _item_group, _rate in SKUS:
        _link_crm_product(item_code, item_code)

    print("\n-- Verification --")
    item_count = frappe.db.count("Item")
    price_count = frappe.db.count("Item Price")
    linked_val = frappe.db.get_value("CRM Product", "CV-HIMS-SUB-CORE", "erpnext_item_code")
    print(f"  frappe.db.count('Item')       = {item_count}")
    print(f"  frappe.db.count('Item Price') = {price_count}")
    print(f"  CRM Product CV-HIMS-SUB-CORE.erpnext_item_code = {linked_val!r}")
    print("\n=== Done ===\n")
