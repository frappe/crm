"""
Synthetic data generator for CRM Sales Hierarchy permission testing.

Run with:
  bench --site erpnext.localhost execute crm.scripts.seed_hierarchy_demo --kwargs '{"reset": true}'

What it creates
---------------
Hierarchy (3 tiers):
  Regional Manager  (sarah.rm@crmdemo.test)
  ├── Area Manager  (james.am@crmdemo.test)
  │   ├── Sales Rep (alice.rep@crmdemo.test)
  │   └── Sales Rep (bob.rep@crmdemo.test)
  └── Area Manager  (kate.am@crmdemo.test)
      ├── Sales Rep (charlie.rep@crmdemo.test)
      └── Sales Rep (diana.rep@crmdemo.test)
  [outsider user]   (oliver.out@crmdemo.test)  — NOT in hierarchy

Leads:   ~40 records spread across the six reps/managers
Deals:   ~30 records spread across the six reps/managers
ToDos:   a handful of cross-assignments (e.g. RM assigned a lead owned by rep)
Settings: enables enable_sales_hierarchy flag
"""

import random

import frappe
from frappe.utils.nestedset import rebuild_tree

# ------------------------------------------------------------------
# Config
# ------------------------------------------------------------------

DOMAIN = "crmdemo.test"

USERS = [
    {"email": f"sarah.rm@{DOMAIN}", "name": "Sarah RM", "role": "Sales Manager"},
    {"email": f"james.am@{DOMAIN}", "name": "James AM", "role": "Sales Manager"},
    {"email": f"kate.am@{DOMAIN}", "name": "Kate AM", "role": "Sales Manager"},
    {"email": f"alice.rep@{DOMAIN}", "name": "Alice Rep", "role": "Sales User"},
    {"email": f"bob.rep@{DOMAIN}", "name": "Bob Rep", "role": "Sales User"},
    {"email": f"charlie.rep@{DOMAIN}", "name": "Charlie Rep", "role": "Sales User"},
    {"email": f"diana.rep@{DOMAIN}", "name": "Diana Rep", "role": "Sales User"},
    {"email": f"oliver.out@{DOMAIN}", "name": "Oliver Outsider", "role": "Sales User"},
]

HIERARCHY = [
    # (node_name, user_email, reports_to_name, is_group)
    ("Regional Manager", f"sarah.rm@{DOMAIN}", None, 1),
    ("James Area", f"james.am@{DOMAIN}", "Regional Manager", 1),
    ("Kate Area", f"kate.am@{DOMAIN}", "Regional Manager", 1),
    ("Alice", f"alice.rep@{DOMAIN}", "James Area", 0),
    ("Bob", f"bob.rep@{DOMAIN}", "James Area", 0),
    ("Charlie", f"charlie.rep@{DOMAIN}", "Kate Area", 0),
    ("Diana", f"diana.rep@{DOMAIN}", "Kate Area", 0),
]

LEAD_SOURCES = ["Email", "Existing Customer", "Reference", "Advertisement", "Cold Calling", "Exhibition", "Facebook"]
LEAD_STATUSES = ["New", "Contacted", "Nurture", "Qualified"]
DEAL_STATUSES_BY_TYPE = {"Won": [], "Lost": [], "Open": []}  # filled from DB

COMPANIES = [
    "Acme Corp", "Globex Industries", "Initech", "Umbrella Ltd", "Stark Enterprises",
    "Wayne Industries", "Vought International", "Umbrella Corp", "Cyberdyne Systems", "Oscorp",
]

FIRST_NAMES = [
    "Liam", "Olivia", "Noah", "Emma", "Oliver", "Ava", "William", "Sophia",
    "Elijah", "Isabella", "James", "Charlotte", "Benjamin", "Amelia", "Lucas",
]
LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller",
    "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez",
]


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------


def make_user(email, full_name, role):
    if frappe.db.exists("User", email):
        return frappe.get_doc("User", email)
    first, *rest = full_name.split()
    last = rest[-1] if rest else ""
    u = frappe.get_doc(
        {
            "doctype": "User",
            "email": email,
            "first_name": first,
            "last_name": last,
            "send_welcome_email": 0,
            "enabled": 1,
        }
    ).insert(ignore_permissions=True)
    u.add_roles(role)
    print(f"  Created user: {email} [{role}]")
    return u


def make_node(user, reports_to_docname, is_group=0):
    existing = frappe.db.get_value("CRM Sales Hierarchy", {"user": user}, "name")
    if existing:
        return frappe.get_doc("CRM Sales Hierarchy", existing)
    doc = frappe.get_doc(
        {
            "doctype": "CRM Sales Hierarchy",
            "user": user,
            "reports_to": reports_to_docname,
            "enabled": 1,
            "is_group": is_group,
        }
    ).insert(ignore_permissions=True)
    print(f"  Created node: ({user}) -> {reports_to_docname or 'root'}")
    return doc


def random_lead(owner_email):
    first = random.choice(FIRST_NAMES)
    last = random.choice(LAST_NAMES)
    doc = frappe.get_doc(
        {
            "doctype": "CRM Lead",
            "first_name": first,
            "last_name": last,
            "email": f"{first.lower()}.{last.lower()}.{random.randint(100,999)}@example.com",
            "lead_owner": owner_email,
            "source": random.choice(LEAD_SOURCES),
            "status": random.choice(LEAD_STATUSES),
            "organization": random.choice(COMPANIES),
        }
    )
    doc.flags.ignore_mandatory = True
    doc.insert(ignore_permissions=True)
    return doc


def ensure_organizations():
    orgs = []
    for name in COMPANIES:
        if not frappe.db.exists("CRM Organization", name):
            frappe.get_doc(
                {"doctype": "CRM Organization", "organization_name": name}
            ).insert(ignore_permissions=True)
        orgs.append(name)
    return orgs


def random_deal(owner_email, statuses, orgs):
    status_name = random.choice(statuses)
    doc = frappe.get_doc(
        {
            "doctype": "CRM Deal",
            "deal_owner": owner_email,
            "organization": random.choice(orgs),
            "status": status_name,
            "deal_value": round(random.uniform(5000, 200000), 2),
        }
    )
    doc.flags.ignore_mandatory = True
    doc.insert(ignore_permissions=True)
    return doc


def assign_todo(doctype, docname, assigned_to):
    frappe.get_doc(
        {
            "doctype": "ToDo",
            "reference_type": doctype,
            "reference_name": docname,
            "allocated_to": assigned_to,
            "status": "Open",
            "description": f"Follow up on {docname}",
        }
    ).insert(ignore_permissions=True)


def teardown():
    print("\n[teardown] removing previously seeded data…")
    for _, user_email, *_ in HIERARCHY:
        docname = frappe.db.get_value("CRM Sales Hierarchy", {"user": user_email}, "name")
        if docname:
            frappe.delete_doc("CRM Sales Hierarchy", docname, ignore_permissions=True, force=True)
    for email in [u["email"] for u in USERS]:
        if frappe.db.exists("User", email):
            frappe.delete_doc("User", email, ignore_permissions=True, force=True)
    frappe.db.commit()  # nosemgrep
    print("  Done.")


# ------------------------------------------------------------------
# Main entry point
# ------------------------------------------------------------------


def execute(reset=False):
    if reset:
        teardown()

    print("\n=== CRM Sales Hierarchy: synthetic data generator ===\n")

    # 1. Users
    print("[1/5] Creating users…")
    for u in USERS:
        make_user(u["email"], u["name"], u["role"])
    frappe.db.commit()  # nosemgrep

    # 2. Hierarchy
    print("\n[2/5] Building hierarchy…")
    node_docnames = {}  # label -> docname
    for node_label, user_email, parent_label, is_group in HIERARCHY:
        parent_docname = node_docnames.get(parent_label)
        doc = make_node(user_email, parent_docname, is_group)
        node_docnames[node_label] = doc.name
    rebuild_tree("CRM Sales Hierarchy")
    frappe.db.commit()  # nosemgrep

    # 3. Leads
    print("\n[3/5] Creating leads…")
    rep_users = [u["email"] for u in USERS if u["email"] != f"oliver.out@{DOMAIN}"]
    leads = []
    for _ in range(40):
        owner = random.choice(rep_users)
        lead = random_lead(owner)
        leads.append(lead)
    # A few leads owned by the outsider (to confirm they are invisible to the hierarchy)
    for _ in range(5):
        lead = random_lead(f"oliver.out@{DOMAIN}")
        leads.append(lead)
    frappe.db.commit()  # nosemgrep
    print(f"  Created {len(leads)} leads.")

    # 4. Deals
    print("\n[4/5] Creating deals…")
    all_statuses = frappe.get_all("CRM Deal Status", pluck="name")
    if not all_statuses:
        print("  WARNING: No CRM Deal Status records found. Skipping deals.")
        deals = []
    else:
        deals = []
        orgs = ensure_organizations()
        frappe.db.commit()  # nosemgrep
        # Exclude "Lost" status to avoid mandatory lost_reason validation
        safe_statuses = frappe.get_all(
            "CRM Deal Status", filters={"type": ["!=", "Lost"]}, pluck="name"
        ) or all_statuses
        for _ in range(30):
            owner = random.choice(rep_users)
            deal = random_deal(owner, safe_statuses, orgs)
            deals.append(deal)
        for _ in range(3):
            deal = random_deal(f"oliver.out@{DOMAIN}", safe_statuses, orgs)
            deals.append(deal)
        frappe.db.commit()  # nosemgrep
        print(f"  Created {len(deals)} deals.")

    # 5. Cross-assignments (ToDos)
    print("\n[5/5] Creating cross-team assignments…")
    # RM assigned on a rep1 lead
    if leads:
        assign_todo("CRM Lead", leads[0].name, f"sarah.rm@{DOMAIN}")
        # outsider assigned on a RM-owned lead
        rm_lead = random_lead(f"sarah.rm@{DOMAIN}")
        assign_todo("CRM Lead", rm_lead.name, f"oliver.out@{DOMAIN}")
    if deals:
        assign_todo("CRM Deal", deals[0].name, f"james.am@{DOMAIN}")
    frappe.db.commit()  # nosemgrep
    print("  Created 3 ToDo cross-assignments.")

    # 6. Enable feature flag
    print("\n[+] Enabling 'enable_sales_hierarchy' in FCRM Settings…")
    settings = frappe.get_single("FCRM Settings")
    settings.enable_sales_hierarchy = 1
    settings.save(ignore_permissions=True)
    frappe.db.commit()  # nosemgrep

    # 7. Summary
    print("\n=== Done! ===")
    print(
        """
Hierarchy
─────────
sarah.rm@{d}       ← Regional Manager (sees everyone below)
├── james.am@{d}   ← Area Manager (sees Alice + Bob)
│   ├── alice.rep@{d}
│   └── bob.rep@{d}
└── kate.am@{d}    ← Area Manager (sees Charlie + Diana)
    ├── charlie.rep@{d}
    └── diana.rep@{d}

oliver.out@{d}     ← NOT in hierarchy (sees only own records)

Password for all demo users: demo123
(set manually via Desk → User or via bench set-user-password)
""".format(d=DOMAIN)
    )
    print("Feature flag 'Enable Sales Hierarchy Permissions' is now ON.\n")
