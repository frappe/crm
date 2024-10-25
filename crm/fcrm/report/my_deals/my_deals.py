# Copyright (c) 2024, Korecent and contributors
# For license information, please see license.txt

import frappe

def execute(filters=None):
    # Define columns for the report
    columns = [
        {"label": "Organization", "fieldname": "organization", "fieldtype": "Data", "width": 150},
        {"label": "Contact", "fieldname": "contact", "fieldtype": "Data", "width": 150},
        {"label": "Status", "fieldname": "status", "fieldtype": "Data", "width": 100},
        {"label": "Email", "fieldname": "email", "fieldtype": "Data", "width": 200},
        {"label": "Assigned To", "fieldname": "assigned_to", "fieldtype": "Data", "width": 150},
        {"label": "Last Email Communication", "fieldname": "last_email_communication", "fieldtype": "Datetime", "width": 180}
    ]
    
    # Fetch data
    data = get_assigned_deals(filters)
    return columns, data

def get_assigned_deals(filters):
    # Current user or user from filter 
    user = filters.get("user") or frappe.session.user

    conditions = []
    
    # Add condition for status if provided
    if filters.get("status"):
        conditions.append(f"deal.status = %(status)s")
    
    # Add condition for organization if provided
    if filters.get("organization"):
        conditions.append(f"deal.organization = %(organization)s")

    # Build the WHERE clause
    where_clause = ""
    if conditions:
        where_clause = "AND " + " AND ".join(conditions)

    # Execute the SQL query to fetch the assigned deals
    return frappe.db.sql("""
        SELECT DISTINCT
            deal.name,
            deal.contact,
            deal.organization,
            deal.status,
            deal.email,
            deal.deal_owner,
            GROUP_CONCAT(DISTINCT ass.allocated_to) as assigned_to,
            (
                SELECT MAX(comm.creation) 
                FROM `tabCommunication` AS comm 
                WHERE comm.reference_doctype = 'CRM Deal' 
                AND comm.reference_name = deal.name 
                AND comm.communication_medium = 'Email'
            ) AS last_email_communication
        FROM
            `tabCRM Deal` AS deal
        LEFT JOIN
            `tabToDo` AS ass
            ON ass.reference_type = 'CRM Deal' 
            AND ass.reference_name = deal.name
        WHERE
            (deal.deal_owner = %(user)s OR ass.allocated_to = %(user)s)
            {where_clause}
        GROUP BY
            deal.name,
            deal.contact,
            deal.organization,
            deal.status,
            deal.email,
            deal.deal_owner
        ORDER BY 
            deal.name
    """.format(where_clause=where_clause), {
        "user": user,
        "status": filters.get("status"),
        "organization": filters.get("organization")
    }, as_dict=True)
