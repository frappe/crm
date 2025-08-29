import frappe

try:
    from frappe.integrations.frappe_providers.frappecloud_billing import is_fc_site
except ImportError:
    def is_fc_site() -> bool:
        try:
            is_system_manager = frappe.get_roles(frappe.session.user).count("System Manager")
            return bool(is_system_manager and frappe.conf.get("fc_communication_secret"))
        except Exception:
            return False