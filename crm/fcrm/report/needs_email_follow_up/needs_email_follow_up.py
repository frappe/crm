# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import add_days, now_datetime

def execute(filters=None):
    if not filters:
        filters = {}

    # Set N-days as default 7 if not provided
    n_days = filters.get("n_days", 7)
    
    # Get the current user if not provided
    current_user = frappe.session.user if not filters.get("assigned_to") else filters.get("assigned_to")

    # Calculate the date for "N days ago"
    follow_up_threshold = add_days(now_datetime(), -n_days)

    # Query to fetch leads
    leads = frappe.db.sql("""
        SELECT 
            lead.lead_name as lead_name, 
            lead.organization as organization,
            lead.status as status, 
            lead.email as email,
            lead.lead_owner as assigned_to,
            communication.communication_date as last_email_date
        FROM `tabCRM Lead` lead
        LEFT JOIN `tabCommunication` communication 
            ON communication.reference_doctype = 'CRM Lead' 
            AND communication.reference_name = lead.name
            AND communication.communication_type = 'Communication' 
            AND communication.communication_medium = 'Email'
        WHERE 
            lead.lead_owner = %(assigned_to)s
            AND communication.communication_date IS NOT NULL
            AND communication.communication_date <= %(threshold_date)s
            AND lead.status LIKE %(status)s
        ORDER BY communication.communication_date ASC
    """, {
        "assigned_to": current_user,
        "threshold_date": follow_up_threshold,
        "status": f"%{filters.get('status', '')}%"
    }, as_dict=True)

    # Define the report columns
    columns = [
        {"label": "Lead Name", "fieldname": "lead_name", "fieldtype": "Data", "width": 180},
        {"label": "Organization", "fieldname": "organization", "fieldtype": "Data", "width": 180},
        {"label": "Status", "fieldname": "status", "fieldtype": "Data", "width": 100},
        {"label": "Email", "fieldname": "email", "fieldtype": "Data", "width": 180},
        {"label": "Assigned To", "fieldname": "assigned_to", "fieldtype": "Data", "width": 120},
        {"label": "Last Email Communication (Day/Time)", "fieldname": "last_email_date", "fieldtype": "Datetime", "width": 180},
    ]

    data = []
    for lead in leads:
        data.append({
            "lead_name": lead.lead_name,
            "organization": lead.organization,
            "status": lead.status,
            "email": lead.email,
            "assigned_to": lead.assigned_to,
            "last_email_date": lead.last_email_date
        })

    return columns, data
