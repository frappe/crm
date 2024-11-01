# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _

def execute(filters=None):
	columns, data = get_columns(), get_data(filters)
	return columns, data

def get_data(filters):
	conditions = get_filter_conditions(filters)

    #fetch deals data
	deals_list = frappe.db.sql(f"""SELECT organization, name, status,
									    close_date,annual_revenue,probability,
									   (annual_revenue * probability / 100) AS weighted_value
							       FROM `tabCRM Deal`
							       WHERE status != 'Closed' {conditions} """,debug =1, as_dict=1)
	for deals in deals_list:
		#fetch deal elements list for particular deal
		deal_element_list = [d['deal_elements'] for d in 
		                    frappe.db.sql(f"""SELECT deal_elements 
					                          FROM `tabCRM Deal Elements` 
					                          WHERE parent = "{deals['name']}" """, as_dict=1)]
		
		#deal elements converted into string type
		if deal_element_list and len(deal_element_list) > 0:
			deals.update({"deal_elements":', '.join(deal_element_list)})
	return deals_list

def get_filter_conditions(filters):
	conditions = ""
	if filters.status:
		conditions += f"and status = '{filters.status}'"
	return conditions


def get_columns():
	return [
		{"fieldname": "organization", "label": _("Organization"), "fieldtype": "Data", "width": 210},
		{"fieldname": "deal_elements", "label": _("Deal Elements"), "fieldtype": "Data", "width": 250},
		{"fieldname": "status", "label": _("Status"), "fieldtype": "Link","options": "CRM Deal Status", "width": 180},
		{"fieldname": "close_date", "label": _("Close Date"), "fieldtype": "Date", "width": 120},
		{"fieldname": "annual_revenue", "label": _("Annual Value"), "fieldtype": "Currency", "width": 170},
		{"fieldname": "probability", "label": _("Probability (%)"), "fieldtype": "Percent", "width": 100},
		{"fieldname": "weighted_value", "label": _("Weighted Value"), "fieldtype": "Currency", "width": 170},
	]

