# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and Contributors
# GNU GPLv3 License. See license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils.telemetry import capture

no_cache = 1


def get_context(context):
    csrf_token = frappe.sessions.get_csrf_token()
    frappe.db.commit()
    if frappe.session.user != "Guest":
        capture("active_site", "crm")
    context.csrf_token = csrf_token
