# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and Contributors
# GNU GPLv3 License. See license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils.telemetry import capture

no_cache = 1


def get_context():
    frappe.db.commit()
    context = frappe._dict()
    context.boot = get_boot()
    if frappe.session.user != "Guest":
        capture("active_site", "crm")
    return context


@frappe.whitelist(methods=["POST"], allow_guest=True)
def get_context_for_dev():
    if not frappe.conf.developer_mode:
        frappe.throw("This method is only meant for developer mode")
    return get_boot()


def get_boot():
    return frappe._dict(
        {
            "frappe_version": frappe.__version__,
            "default_route": get_default_route(),
            "site_name": frappe.local.site,
            "read_only_mode": frappe.flags.read_only,
            "csrf_token": frappe.sessions.get_csrf_token(),
        }
    )


def get_default_route():
    return "/crm"
