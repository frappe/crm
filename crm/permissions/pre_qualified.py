import frappe


def get_permission_query(user=None):
    if not user:
        user = frappe.session.user
    if "System Manager" in frappe.get_roles(user) or user == "Administrator":
        return ""
    assigned = frappe.db.get_value("User", user, "assigned_network") or ""
    if not assigned:
        return "1=0"
    return "`tabCRM Pre-Qualified Facility`.`network` = %s" % frappe.db.escape(assigned)
