# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe

def execute(filters=None):
    # Define columns for the report
    columns = [
        {"label": "Name", "fieldname": "lead_name", "fieldtype": "Data", "width": 150},
        {"label": "Organization", "fieldname": "organization", "fieldtype": "Data", "width": 150},
        {"label": "Status", "fieldname": "status", "fieldtype": "Data", "width": 100},
        {"label": "Email", "fieldname": "email", "fieldtype": "Data", "width": 200},
        {"label": "Lead Owner", "fieldname": "lead_owner", "fieldtype": "Link", "options": "User", "width": 150},
        {"label": "Assigned To", "fieldname": "assigned_to", "fieldtype": "Data", "width": 150},
        {"label": "Last Email Communication", "fieldname": "last_email_communication", "fieldtype": "Datetime", "width": 180}
    ]

    # Fetch data
    data = get_assigned_leads(filters)
    return columns, data

def get_assigned_leads(filters):
    # Current user or user from filter
    allocated_to = filters.get("user") or frappe.session.user

    # Initialize conditions for the WHERE clause
    conditions = ""

    # condition for status
    if filters.get("status"):
        conditions += f""" AND lead.status = '{filters.get("status")}' """

    # condition for organization
    if filters.get("organization"):
        conditions += f""" AND lead.organization = '{filters.get("organization")}' """

    # Execute the SQL query to fetch the leads
    return frappe.db.sql("""
        SELECT DISTINCT
            lead.name,
            lead.lead_name,
            lead.organization,
            lead.status,
            lead.email,
            lead.lead_owner,
            GROUP_CONCAT(DISTINCT ass.allocated_to) as assigned_to,
            (
                SELECT MAX(comm.creation)
                FROM `tabCommunication` AS comm
                WHERE comm.reference_doctype = 'CRM Lead' 
                AND comm.reference_name = lead.name 
                AND comm.communication_medium = 'Email'
            ) AS last_email_communication
        FROM
            `tabCRM Lead` AS lead
        LEFT JOIN
            `tabToDo` AS ass
            ON ass.reference_type = 'CRM Lead' 
            AND ass.reference_name = lead.name
        WHERE
            (lead.lead_owner = %(allocated_to)s OR ass.allocated_to = %(allocated_to)s)
            {conditions}
        GROUP BY
            lead.name,
            lead.lead_name,
            lead.organization,
            lead.status,
            lead.email,
            lead.lead_owner
        ORDER BY 
            lead.name
    """.format(conditions=conditions), {
        "allocated_to": allocated_to
    }, as_dict=True)