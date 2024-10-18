# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt
# Scrum-74 - Recently assigned deal report (10-17-2024)-Anuradha
import frappe
from frappe import _
from datetime import datetime, date

def execute(filters):
    columns, data = [], []
    columns = get_columns()
    data = get_data(filters)
    return columns, data

def get_columns():
    return [
        {"fieldname": "deal_name", "label": _("Deal Name"), "fieldtype": "Link","options": "CRM Deal", "width": 220},
        {"fieldname": "organization", "label": _("Organization"), "fieldtype": "Data", "width": 200},
        {"fieldname": "status", "label": _("Status"), "fieldtype": "Link","options": "CRM Deal Status", "width": 200},
        {"fieldname": "email_id", "label": _("Email Id"), "fieldtype": "Data", "width": 200},
        {"fieldname": "assigned_to", "label": _("Assigned To"), "fieldtype": "Link", "options": "User", "width": 200},
        {"fieldname": "time_assigned", "label": _("Time Assigned"), "fieldtype": "Data", "width": 200}
    ]

def get_data(filters):
    #get filter condition
    conditions = get_filter_conditions(filters)

    #fetch deal data order by creation date
    deal_details = frappe.db.sql(f"""select  D.name as deal_name, D.organization as organization, 
                                    D.status as status, D.email as email_id, D.creation as creation, 
                                    t.allocated_to AS assigned_to
                                    from `tabCRM Deal` as D LEFT JOIN `tabToDo` t
                                    ON t.reference_type = 'CRM Deal' AND t.reference_name = D.name
                                    where D.docstatus < 2 {conditions} order by D.creation desc """,as_dict=1)
    
    #fetch time if creation date is today else fetch date
    for deal in deal_details:
        email  = frappe.db.get_value("CRM Contacts", {'parent':deal['deal_name'], 'is_primary':1}, 'email') 
        if email:
            deal['email'] = email
        else:
            deal['email'] = frappe.db.get_value("CRM Contacts", {'parent':deal['deal_name']}, 'email') or ''
        deal['time_assigned'] = deal.get('creation').date()
        
    return deal_details

def get_filter_conditions(filters):
    conditions = ""
    if filters.from_date:
        conditions += f"and date(D.creation) >= '{filters.from_date}'"
    if filters.to_date:
        conditions += f" and date(D.creation) <= '{filters.to_date}'"
    if filters.assigned_to:
        conditions += f" and t.allocated_to = '{filters.assigned_to}'"
    return conditions
