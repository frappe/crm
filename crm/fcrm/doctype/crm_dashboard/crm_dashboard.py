# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class CRMDashboard(Document):
	pass


def default_manager_dashboard_layout():
	"""
	Returns the default layout for the CRM Manager Dashboard.
	"""
	return '[{"name": "total_leads", "type": "number_chart", "tooltip": "Total number of leads", "layout": {"x": 0, "y": 0, "w": 4, "h": 2, "i": "total_leads"}}, {"name": "ongoing_deals", "type": "number_chart", "tooltip": "Total number of ongoing deals", "layout": {"x": 4, "y": 0, "w": 4, "h": 2, "i": "ongoing_deals"}}, {"name": "average_ongoing_deal_value", "type": "number_chart", "tooltip": "Average value of ongoing deals", "layout": {"x": 8, "y": 0, "w": 4, "h": 2, "i": "average_ongoing_deal_value"}}, {"name": "won_deals", "type": "number_chart", "tooltip": "Total number of won deals", "layout": {"x": 12, "y": 0, "w": 4, "h": 2, "i": "won_deals"}}, {"name": "average_won_deal_value", "type": "number_chart", "tooltip": "Average value of won deals", "layout": {"x": 16, "y": 0, "w": 4, "h": 2, "i": "average_won_deal_value"}}, {"name": "average_deal_value", "type": "number_chart", "tooltip": "Average deal value of ongoing and won deals", "layout": {"x": 0, "y": 2, "w": 4, "h": 2, "i": "average_deal_value"}}, {"name": "average_time_to_close_a_lead", "type": "number_chart", "tooltip": "Average time taken to close a lead", "layout": {"x": 4, "y": 2, "w": 4, "h": 2, "i": "average_time_to_close_a_lead"}}, {"name": "average_time_to_close_a_deal", "type": "number_chart", "layout": {"x": 8, "y": 2, "w": 4, "h": 2, "i": "average_time_to_close_a_deal"}}, {"name": "blank_card", "type": "blank_card", "layout": {"x": 12, "y": 2, "w": 8, "h": 2, "i": "blank_card"}}, {"name": "sales_trend", "type": "axis_chart", "layout": {"x": 0, "y": 4, "w": 10, "h": 7, "i": "sales_trend"}}, {"name": "forecasted_revenue", "type": "axis_chart", "layout": {"x": 10, "y": 4, "w": 10, "h": 7, "i": "forecasted_revenue"}}, {"name": "funnel_conversion", "type": "axis_chart", "layout": {"x": 0, "y": 11, "w": 10, "h": 7, "i": "funnel_conversion"}}, {"name": "deals_by_stage_axis", "type": "axis_chart", "layout": {"x": 10, "y": 11, "w": 10, "h": 7, "i": "deals_by_stage_axis"}}, {"name": "deals_by_stage_donut", "type": "donut_chart", "layout": {"x": 0, "y": 18, "w": 10, "h": 7, "i": "deals_by_stage_donut"}}, {"name": "lost_deal_reasons", "type": "axis_chart", "layout": {"x": 10, "y": 18, "w": 10, "h": 7, "i": "lost_deal_reasons"}}, {"name": "leads_by_source", "type": "donut_chart", "layout": {"x": 0, "y": 25, "w": 10, "h": 7, "i": "leads_by_source"}}, {"name": "deals_by_source", "type": "donut_chart", "layout": {"x": 10, "y": 25, "w": 10, "h": 7, "i": "deals_by_source"}}, {"name": "deals_by_territory", "type": "axis_chart", "layout": {"x": 0, "y": 32, "w": 10, "h": 7, "i": "deals_by_territory"}}, {"name": "deals_by_salesperson", "type": "axis_chart", "layout": {"x": 10, "y": 32, "w": 10, "h": 7, "i": "deals_by_salesperson"}}]'


def create_default_manager_dashboard():
	"""
	Creates the default CRM Manager Dashboard if it does not exist.
	"""
	if not frappe.db.exists("CRM Dashboard", "Manager Dashboard"):
		doc = frappe.new_doc("CRM Dashboard")
		doc.title = "Manager Dashboard"
		doc.layout = default_manager_dashboard_layout()
		doc.insert(ignore_permissions=True)
	return doc.layout
