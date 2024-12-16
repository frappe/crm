# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and Contributors
# GNU GPLv3 License. See license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import cint, get_system_timezone
from frappe.utils.telemetry import capture

# COMPATIBILITY NOTE:
# In Frappe develop branch, locale-related functions were moved to frappe.locale
# In version-15, these functions are still in frappe.utils.data
# We try the new location first, then fall back to the old location

try:
    from frappe.locale import (
        get_date_format,
        get_first_day_of_the_week,
        get_number_format,
        get_time_format,
    )
    NUMBER_FORMAT_FUNCTION_TAKES_ARG = False
except ImportError:
    from frappe.utils.data import (
        get_user_date_format as get_date_format,
        get_first_day_of_the_week,
        get_number_format_info as get_number_format, 
        get_user_time_format as get_time_format,
    )
    NUMBER_FORMAT_FUNCTION_TAKES_ARG = True

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
    number_format = get_number_format("# ###,##") if NUMBER_FORMAT_FUNCTION_TAKES_ARG else get_number_format()
    number_format_string = number_format.string if hasattr(number_format, 'string') else number_format
    
    return frappe._dict(
        {
            "frappe_version": frappe.__version__,
            "default_route": get_default_route(),
            "site_name": frappe.local.site,
            "read_only_mode": frappe.flags.read_only,
            "csrf_token": frappe.sessions.get_csrf_token(),
            "setup_complete": cint(frappe.get_system_settings("setup_complete")),
            "sysdefaults": {
                "float_precision": cint(frappe.get_system_settings("float_precision"))
                or 2,
                "date_format": get_date_format(),
                "time_format": get_time_format(),
                "first_day_of_the_week": get_first_day_of_the_week(),
                "number_format": number_format_string,
            },
            "timezone": {
                "system": get_system_timezone(),
                "user": frappe.db.get_value("User", frappe.session.user, "time_zone")
                or get_system_timezone(),
            },
        }
    )


def get_default_route():
    return "/crm"
