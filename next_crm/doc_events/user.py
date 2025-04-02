import frappe
from frappe import _


def validate_user(doc, event):
    if (
        frappe.conf.demo_username
        and frappe.session.user == frappe.conf.demo_username
        and doc.new_password
    ):
        frappe.throw(
            _("Password cannot be reset by Demo User {}").format(
                frappe.bold(frappe.conf.demo_username)
            ),
            frappe.PermissionError,
        )
