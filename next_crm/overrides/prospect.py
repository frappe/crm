# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt
import frappe
from erpnext.crm.doctype.prospect.prospect import Prospect
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

    def create_opportunity(self):
        from erpnext.crm.doctype.prospect.prospect import make_opportunity

        opportunity = make_opportunity(self.name)

        opportunity.insert(ignore_permissions=True)
        return opportunity.name


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
    opportunity = prospect.create_opportunity()
    return opportunity
