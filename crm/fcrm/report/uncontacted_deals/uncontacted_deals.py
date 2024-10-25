# Copyright (c) 2024, Korecent and contributors
# For license information, please see license.txt
# Copyright (c) 2024, Korecent and contributors
# For license information, please see license.txt

import frappe

def execute(filters=None):
    # Define columns for the report
    columns = [
        {"label": "Organization", "fieldname": "organization", "fieldtype": "Data", "width": 150},
        {"label": "Contact", "fieldname": "contact", "fieldtype": "Data", "width": 100},
        {"label": "Status", "fieldname": "status", "fieldtype": "Data", "width": 100},
        {"label": "Email", "fieldname": "email", "fieldtype": "Data", "width": 200},
        {"label": "Deal Owner", "fieldname": "deal_owner", "fieldtype": "Link", "options": "User", "width": 150},
        {"label": "Assigned To", "fieldname": "assigned_to", "fieldtype": "Data", "width": 150},
        {"label": "Time Assigned", "fieldname": "time_assigned", "fieldtype": "Datetime", "width": 180}
    ]

    # Fetch data based on filters
    data = get_uncontacted_deals(filters)
    return columns, data

def get_uncontacted_deals(filters):
    # Default to the current user if no user is provided in the filters
    assigned_to = filters.get("user") or frappe.session.user

    conditions = ""
    
    # Add condition for organization if provided
    if filters.get("organization"):
        conditions += f""" AND deal.organization = '{filters.get("organization")}' """

    # Modified query to show deals where the user is either the owner or an assignee
    return frappe.db.sql(f"""
        SELECT DISTINCT
            deal.name,
            deal.organization,
            deal.contact,
            deal.status,
            deal.email,
            deal.deal_owner,
            GROUP_CONCAT(DISTINCT ass.allocated_to) as assigned_to,
            MIN(ass.creation) as time_assigned
        FROM
            `tabCRM Deal` AS deal
        LEFT JOIN
            `tabToDo` AS ass
            ON ass.reference_type = 'CRM Deal'
            AND ass.reference_name = deal.name
        LEFT JOIN
            `tabCommunication` AS comm
            ON comm.reference_doctype = 'CRM Deal'
            AND comm.reference_name = deal.name
            AND (comm.communication_medium = 'Email' 
                OR comm.communication_medium = 'Phone')
        WHERE
            (deal.deal_owner = %(user)s OR ass.allocated_to = %(user)s)
            AND comm.name IS NULL
            {conditions}
        GROUP BY
            deal.name,
            deal.organization,
            deal.contact,
            deal.status,
            deal.email,
            deal.deal_owner
        ORDER BY 
            deal.name
    """, {
        "user": assigned_to,
        "conditions": conditions
    }, as_dict=True)