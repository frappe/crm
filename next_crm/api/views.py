import frappe
from pypika import Criterion


@frappe.whitelist()
def get_views(doctype):
    View = frappe.qb.DocType("CRM View Settings")
    query = (
        frappe.qb.from_(View)
        .select("*")
        .where(Criterion.any([View.user == "", View.user == frappe.session.user]))
    )
    if doctype:
        query = query.where(View.dt == doctype)
    views = query.run(as_dict=True)
    return views


@frappe.whitelist()
def get_default_open_view():

    views = frappe.get_all(
        "CRM View Settings",
        fields=["dt", "type", "user", "is_default", "default_open_view"],
        filters={
            "user": frappe.session.user,
            "default_open_view": 1,
            "is_default": 1,
            "dt": ["is", "set"],
        },
    )

    fallback_views = frappe.get_all(
        "CRM View Settings",
        fields=["dt", "type"],
        filters={
            "user": "",
            "default_open_view": 1,
            "is_default": 1,
            "dt": ["is", "set"],
        },
    )

    default_view_object = {}
    for view in views:
        default_view_object[view.dt] = view.type

    for view in fallback_views:
        if not default_view_object[view.dt]:
            default_view_object[view.dt] = view.type

    return default_view_object
