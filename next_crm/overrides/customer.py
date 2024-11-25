# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from erpnext.selling.doctype.customer.customer import Customer


class Customer(Customer):

    @staticmethod
    def default_list_data():
        columns = [
            {
                "label": "Customer",
                "type": "Data",
                "key": "customer_name",
                "width": "16rem",
            },
            {
                "label": "Website",
                "type": "Data",
                "key": "website",
                "width": "14rem",
            },
            {
                "label": "Industry",
                "type": "Link",
                "key": "industry",
                "options": "Industry Type",
                "width": "14rem",
            },
            {
                "label": "Annual Revenue",
                "type": "Currency",
                "key": "annual_revenue",
                "width": "14rem",
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
            "customer_name",
            "image",
            "website",
            "industry",
            "default_currency",
            "annual_revenue",
            "modified",
        ]
        return {"columns": columns, "rows": rows}
