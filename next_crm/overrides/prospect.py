# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt
import frappe
from erpnext.crm.doctype.prospect.prospect import (
    Prospect,
    make_customer,
    make_opportunity,
)
from frappe import _


class Prospect(Prospect):

    @staticmethod
    def default_list_data():
        columns = [
            {
                "label": "Company",
                "type": "Data",
                "key": "company_name",
                "width": "11rem",
            },
            {
                "label": "Annual Revenue",
                "type": "Currency",
                "key": "annual_revenue",
                "width": "9rem",
            },
            {
                "label": "Industry",
                "type": "Link",
                "key": "industry",
                "width": "10rem",
            },
            {
                "label": "Website",
                "type": "Data",
                "key": "website",
                "width": "12rem",
            },
            {
                "label": "Last Modified",
                "type": "Datetime",
                "key": "modified",
                "width": "8rem",
            },
        ]
        rows = [
            "name",
            "company_name",
            "annual_revenue",
            "industry",
            "website",
            "modified",
            "modified",
            "_assign",
        ]
        return {"columns": columns, "rows": rows}

    @staticmethod
    def default_kanban_settings():
        return {
            "column_field": "industry",
            "title_field": "company_name",
            "kanban_fields": '["annual_revenue", "_assign", "modified"]',
        }


@frappe.whitelist()
def create_opportunity(prospect, doc=None):
    if (
        not (doc and doc.flags.get("ignore_permissions"))
        and not frappe.has_permission("Prospect", "write", prospect)
    ) or not frappe.has_permission("Opportunity", "create"):
        frappe.throw(
            _("Not allowed to create Opportunity from Prospect"), frappe.PermissionError
        )

    prospect = frappe.get_cached_doc("Prospect", prospect)
    opportunity = make_opportunity(prospect.name)
    opportunity.insert()
    return opportunity.name


@frappe.whitelist()
def create_customer(prospect):
    if not frappe.has_permission("Customer", "create"):
        frappe.throw(
            _("Not allowed to create Customer from Prospect"), frappe.PermissionError
        )

    prospect = frappe.get_cached_doc("Prospect", prospect)
    customer = make_customer(prospect.name)
    customer.insert()
    return customer.name
