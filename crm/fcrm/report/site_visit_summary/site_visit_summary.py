# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    chart = get_chart_data(data)
    summary = get_summary_data(data)
    
    return columns, data, None, chart, summary


def get_columns():
    return [
        {
            "label": _("Site Visit"),
            "fieldname": "name",
            "fieldtype": "Link",
            "options": "CRM Site Visit",
            "width": 120
        },
        {
            "label": _("Date"),
            "fieldname": "visit_date",
            "fieldtype": "Date",
            "width": 100
        },
        {
            "label": _("Sales Person"),
            "fieldname": "sales_person",
            "fieldtype": "Link",
            "options": "User",
            "width": 120
        },
        {
            "label": _("Customer"),
            "fieldname": "reference_title",
            "fieldtype": "Data",
            "width": 150
        },
        {
            "label": _("Type"),
            "fieldname": "visit_type",
            "fieldtype": "Data",
            "width": 120
        },
        {
            "label": _("Status"),
            "fieldname": "status",
            "fieldtype": "Data",
            "width": 100
        },
        {
            "label": _("Duration (hrs)"),
            "fieldname": "duration_hours",
            "fieldtype": "Float",
            "width": 100,
            "precision": 2
        },
        {
            "label": _("Lead Quality"),
            "fieldname": "lead_quality",
            "fieldtype": "Data",
            "width": 100
        },
        {
            "label": _("Potential Value"),
            "fieldname": "potential_value",
            "fieldtype": "Currency",
            "width": 120
        },
        {
            "label": _("Success %"),
            "fieldname": "probability_percentage",
            "fieldtype": "Percent",
            "width": 80
        },
        {
            "label": _("City"),
            "fieldname": "city",
            "fieldtype": "Data",
            "width": 100
        }
    ]


def get_data(filters):
    conditions = get_conditions(filters)
    
    data = frappe.db.sql(f"""
        SELECT 
            name, visit_date, sales_person, reference_title, visit_type,
            status, total_duration, lead_quality, potential_value,
            probability_percentage, city,
            CASE 
                WHEN total_duration > 0 THEN ROUND(total_duration/3600, 2)
                ELSE 0
            END as duration_hours
        FROM `tabCRM Site Visit`
        WHERE docstatus < 2 {conditions}
        ORDER BY visit_date DESC
    """, as_dict=1)
    
    return data


def get_conditions(filters):
    conditions = ""
    
    if filters.get("from_date"):
        conditions += f" AND visit_date >= '{filters.get('from_date')}'"
    
    if filters.get("to_date"):
        conditions += f" AND visit_date <= '{filters.get('to_date')}'"
    
    if filters.get("sales_person"):
        conditions += f" AND sales_person = '{filters.get('sales_person')}'"
    
    if filters.get("status"):
        conditions += f" AND status = '{filters.get('status')}'"
    
    if filters.get("visit_type"):
        conditions += f" AND visit_type = '{filters.get('visit_type')}'"
    
    if filters.get("lead_quality"):
        conditions += f" AND lead_quality = '{filters.get('lead_quality')}'"
    
    return conditions


def get_chart_data(data):
    if not data:
        return None
    
    # Status-wise chart
    status_data = {}
    for row in data:
        status_data[row.status] = status_data.get(row.status, 0) + 1
    
    return {
        "data": {
            "labels": list(status_data.keys()),
            "datasets": [{
                "name": "Site Visits",
                "values": list(status_data.values())
            }]
        },
        "type": "donut",
        "height": 300,
        "colors": ["#28a745", "#ffc107", "#dc3545", "#6c757d", "#17a2b8"]
    }


def get_summary_data(data):
    if not data:
        return []
    
    total_visits = len(data)
    completed_visits = len([d for d in data if d.status == 'Completed'])
    total_duration = sum([d.duration_hours or 0 for d in data])
    total_potential_value = sum([d.potential_value or 0 for d in data])
    hot_leads = len([d for d in data if d.lead_quality == 'Hot'])
    
    avg_duration = total_duration / total_visits if total_visits > 0 else 0
    completion_rate = (completed_visits / total_visits * 100) if total_visits > 0 else 0
    
    return [
        {
            "value": total_visits,
            "label": "Total Visits",
            "indicator": "Blue",
            "datatype": "Int"
        },
        {
            "value": completed_visits,
            "label": "Completed",
            "indicator": "Green",
            "datatype": "Int"
        },
        {
            "value": f"{completion_rate:.1f}%",
            "label": "Completion Rate",
            "indicator": "Green" if completion_rate >= 80 else "Orange",
            "datatype": "Data"
        },
        {
            "value": f"{avg_duration:.1f}h",
            "label": "Avg Duration",
            "indicator": "Blue",
            "datatype": "Data"
        },
        {
            "value": total_potential_value,
            "label": "Total Potential Value",
            "indicator": "Green",
            "datatype": "Currency"
        },
        {
            "value": hot_leads,
            "label": "Hot Leads",
            "indicator": "Red",
            "datatype": "Int"
        }
    ]
