# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _

def execute(filters=None):
	columns = [
		{"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 120},
		{"label": _("Total Value"), "fieldname": "total_value", "fieldtype": "Currency", "width": 150},
		{"label": _("Weighted Value"), "fieldname": "weighted_value", "fieldtype": "Currency", "width": 150}
	]
	data = get_data(filters)
	chart = get_chart_data(data)

	return columns, data, None, chart


def get_data(filters):
	conditions = ""

	# Apply filters for lead owner, date range, and CRM organization
	if filters.get("deal_owner"):
		conditions += f"""AND de.deal_owner = '{filters.get("deal_owner")}' """

	if filters.get("from_date") and filters.get("to_date"):
		conditions += f""" AND de.creation BETWEEN '{filters.get("from_date")}' AND '{filters.get("to_date")}' """

	if filters.get("crm_organization"):
		conditions += f""" AND de.crm_organization = '{filters.get("crm_organization")}' """

	if filters.get("status"):
		conditions += f""" AND de.status = '{filters.get("status")}' """


	sales_stages_data = frappe.db.sql(f"""
		SELECT 
			de.status, 
			SUM(de.annual_revenue) AS total_value, 
			SUM(de.annual_revenue * de.probability / 100) AS weighted_value
		FROM `tabCRM Deal` de
		WHERE de.status != 'Lost'
		{conditions}
		GROUP BY de.status
	""", filters, as_dict=1)

	return sales_stages_data

def get_chart_data(data):
	# Extracting the x-axis and y-axis values from the data
	statuses = [row['status'] for row in data]
	total_values = [row['total_value'] for row in data]
	weighted_values = [row['weighted_value'] for row in data]

	# Define chart data
	chart = {
		"data": {
			"labels": statuses,  # X-axis will be the statuses
			"datasets": [
				{
					"name": _("Total Value"),
					"values": total_values,  
					"chartType": "bar",
					"color": "#7e368d"  
				},
				{
					"name": _("Weighted Value"),
					"values": weighted_values,  # Y-axis for weighted_value
					"chartType": "bar",
					"color": "#ED6396" 
				}
			]
		},
		"type": "bar",  
		"axisOptions": {
			"xIsSeries": 1 
		},
		"barOptions": {
			"stacked": True 
		}
	}

	return chart