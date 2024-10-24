# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import add_days, now_datetime
from frappe import _

def execute(filters=None):
	columns, data = [], []
	columns = get_columns()
	data = get_data(filters)
	return columns, data

def get_data(filters):
	conditions = get_filter_conditions(filters)

	# Get the current user if not provided
	current_user = frappe.session.user if not filters.get("assigned_to") else filters.get("assigned_to")

	# Query to fetch deals
	deal_details = frappe.db.sql(f"""SELECT 
								DISTINCT(deal.name) as deal_name, 
								deal.organization as organization,
								deal.status as status, 
								deal.email as email,
								deal.deal_owner as assigned_to,
								C.communication_date as last_email_date
							FROM `tabCRM Deal` deal
							LEFT JOIN `tabCommunication` as C 
								ON C.reference_doctype = 'CRM Deal' 
								AND C.reference_name = deal.name
								AND C.communication_type = 'Communication' 
								AND C.communication_medium = 'Email'
							WHERE 
								deal.deal_owner = '{current_user}'
								 {conditions}
							ORDER BY C.communication_date ASC""", debug=1, as_dict=True)
	
	for deal in deal_details:
		if not deal['email']:
			email  = frappe.db.get_value("CRM Contacts", {'parent':deal['deal_name'], 'is_primary':1}, 'email') 
			print(f"^^^^^^^^^^^^^^^^^^^^^email {email}")
			if email:
				deal['email'] = email
				print(f"iiiiiiiiiiiiiiiiiiideal['email'] {deal['email']}")
			else:
				deal['email'] = frappe.db.get_value("CRM Contacts", {'parent':deal['deal_name']}, 'email') or ''
				print(f"eeeeeeeeeeeeeeeeeeedeal['email'] {deal['email']}")
	print(f"---------------deal_details {deal_details}")
	return deal_details

def get_columns():
	return [
		{"fieldname": "deal_name", "label": _("Deal Name"), "fieldtype": "Link","options": "CRM Deal", "width": 220},
		{"fieldname": "organization", "label": _("Organization"), "fieldtype": "Data", "width": 200},
		{"fieldname": "status", "label": _("Status"), "fieldtype": "Link","options": "CRM Deal Status", "width": 200},
		{"fieldname": "email", "label": _("Email Id"), "fieldtype": "Data", "width": 200},
		{"fieldname": "assigned_to", "label": _("Assigned To"), "fieldtype": "Link", "options": "User", "width": 200},
		{"fieldname": "last_email_date", "label": _("Last Email Communication (Day/Time)"), "fieldtype": "Data", "width": 200}
	]

def get_filter_conditions(filters):
	conditions = ""
	if filters.from_date:
		conditions += f"and date(C.communication_date) >= '{filters.from_date}'"
	if filters.to_date:
		conditions += f" and date(C.communication_date) <= '{filters.to_date}'"
	if filters.status:
		conditions += f" and deal.status = '{filters.status}'"
	return conditions
