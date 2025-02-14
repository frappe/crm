# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from erpnext.crm.doctype.prospect.prospect import Prospect


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
