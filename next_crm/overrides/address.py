from frappe.contacts.doctype.address.address import Address


class CustomAddress(Address):
    @staticmethod
    def default_list_data():
        columns = [
            {
                "label": "Name",
                "type": "Data",
                "key": "name",
                "width": "10rem",
            },
            {
                "label": "Title",
                "type": "Data",
                "key": "address_title",
                "width": "10rem",
            },
            {
                "label": "Line 1",
                "type": "Data",
                "key": "address_line1",
                "width": "12rem",
            },
            {
                "label": "Address Type",
                "type": "Data",
                "key": "address_type",
                "width": "8rem",
            },
            {
                "label": "Phone",
                "type": "Data",
                "key": "phone",
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
            "address_title",
            "address_line1",
            "address_type",
            "phone",
            "modified",
        ]
        return {"columns": columns, "rows": rows}
