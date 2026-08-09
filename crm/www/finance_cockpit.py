import frappe
from frappe import _
from frappe.translate import get_messages_for_boot, get_translated_doctypes
from frappe.utils import cint, get_system_timezone

no_cache = 1

FINANCE_ROLES = frozenset([
    "Finance Manager", "AR Accountant", "AP Accountant",
    "Accounts Manager", "Accounts User",
    "Sales Manager", "Partner RM",
    "System Manager",
])


def get_context():
    if frappe.session.user == "Guest":
        frappe.local.flags.redirect_location = "/login?redirect-to=/finance-cockpit"
        raise frappe.Redirect

    roles = set(frappe.get_roles(frappe.session.user))
    is_admin = frappe.session.user == "Administrator" or "System Manager" in roles
    if not is_admin and not (roles & FINANCE_ROLES):
        frappe.local.flags.redirect_location = "/access-restricted"
        raise frappe.Redirect

    frappe.db.commit()
    context = frappe._dict()
    context.boot = _get_boot()
    return context


@frappe.whitelist(methods=["POST"], allow_guest=True)
def get_context_for_dev():
    if not frappe.conf.developer_mode:
        frappe.throw(_("This method is only meant for developer mode"))
    return _get_boot()


def _is_fc_site():
    try:
        from frappe.integrations.frappe_providers.frappecloud_billing import is_fc_site
        return is_fc_site()
    except Exception:
        return False


def _get_boot():
    return frappe._dict({
        "frappe_version": frappe.__version__,
        "site_name": frappe.local.site,
        "socketio_port": frappe.conf.socketio_port,
        "read_only_mode": frappe.flags.read_only,
        "csrf_token": frappe.sessions.get_csrf_token(),
        "setup_complete": cint(frappe.get_system_settings("setup_complete")),
        "sysdefaults": frappe.defaults.get_defaults(),
        "is_fc_site": _is_fc_site(),
        "translated_doctypes": get_translated_doctypes(),
        "translated_messages": get_messages_for_boot(),
        "timezone": {
            "system": get_system_timezone(),
            "user": frappe.db.get_value("User", frappe.session.user, "time_zone")
            or get_system_timezone(),
        },
        "session": {
            "user": frappe.session.user,
            "user_email": frappe.session.user,
        },
        "user": {
            "name": frappe.session.user,
            "roles": frappe.get_roles(frappe.session.user),
        },
    })
