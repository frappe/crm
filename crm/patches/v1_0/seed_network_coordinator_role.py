import frappe


def execute():
    # Create Network Coordinator role if not present
    if not frappe.db.exists("Role", "Network Coordinator"):
        frappe.get_doc({
            "doctype": "Role",
            "role_name": "Network Coordinator",
            "desk_access": 1,
        }).insert(ignore_permissions=True)  # SYSTEM-INTERNAL

    # Add assigned_network custom field on User
    if not frappe.db.exists("Custom Field", "User-assigned_network"):
        frappe.get_doc({
            "doctype": "Custom Field",
            "dt": "User",
            "fieldname": "assigned_network",
            "fieldtype": "Data",
            "label": "Assigned Network",
            "insert_after": "last_known_versions",
        }).insert(ignore_permissions=True)  # SYSTEM-INTERNAL
