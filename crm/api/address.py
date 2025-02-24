import frappe

@frappe.whitelist()
def get_default_country():
    """Get default country from System Settings"""
    try:
        return frappe.db.get_single_value('System Settings', 'country', ignore_permissions=True)
    except:
        return 'Russian Federation' 