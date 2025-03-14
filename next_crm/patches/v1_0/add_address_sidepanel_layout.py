import frappe


def execute():
    if frappe.db.exists("CRM Fields Layout", "Address-Side Panel"):
        return

    layout = {
        "doctype": "Address",
        "layout": '[{"label":"Details","opened":true,"fields":["address_title","address_type","address_line1","address_line2","city","county","state","country","pincode","email_id","phone","fax","is_primary_address","is_shipping_address","disabled"],"editingLabel":false}]',
    }

    doc = frappe.new_doc("CRM Fields Layout")
    doc.type = "Side Panel"
    doc.dt = layout["doctype"]
    doc.layout = layout["layout"]
    doc.insert()
