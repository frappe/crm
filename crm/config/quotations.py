from erpnext.selling.doctype.quotation.quotation import Quotation

def default_list_data():
    columns = [
        
        {
            "label": "Party Name",
            "type": "Data",
            "key": "party_name",
            "width": "11rem",
        },
        {
            "label": "Date",
            "type": "Date",
            "key": "transaction_date",
            "align": "right",
            "width": "9rem",
        },
        {
            "label": "Status",
            "type": "Select",
            "key": "status",
            "width": "10rem",
        },
        {
            "label": "ID",
            "type": "Data",
            "key": "name",
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
        "status",
        "title",
        "transaction_date",
        "modified",
        "_assign",
    ]
    return {"columns": columns, "rows": rows}

def default_kanban_settings():
    return {
        "column_field": "status",
        "title_field": "title",
        "kanban_fields": '["order_type", "customer_name", "valid_till", "_assign", "modified"]',
    }

def patch():
    print("Patching Quotation with custom configurations...")
    Quotation.default_list_data = staticmethod(default_list_data)
    Quotation.default_kanban_settings = staticmethod(default_kanban_settings)

patch()