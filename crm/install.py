# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt
from __future__ import unicode_literals
import click
import frappe

from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

def before_install():
	pass

def after_install():
	add_default_lead_statuses()
	add_default_deal_statuses()
	add_default_communication_statuses()
	add_default_fields_layout()
	add_property_setter()
	add_email_template_custom_fields()
	frappe.db.commit()

def add_default_lead_statuses():
	statuses = {
		"New": {
			"color": "gray",
			"position": 1,
		},
		"Contacted": {
			"color": "orange",
			"position": 2,
		},
		"Nurture": {
			"color": "blue",
			"position": 3,
		},
		"Qualified": {
			"color": "green",
			"position": 4,
		},
		"Unqualified": {
			"color": "red",
			"position": 5,
		},
		"Junk": {
			"color": "purple",
			"position": 6,
		},
	}

	for status in statuses:
		if frappe.db.exists("CRM Lead Status", status):
			continue

		doc = frappe.new_doc("CRM Lead Status")
		doc.lead_status = status
		doc.color = statuses[status]["color"]
		doc.position = statuses[status]["position"]
		doc.insert()

def add_default_deal_statuses():
	statuses = {
		"Qualification": {
			"color": "gray",
			"position": 1,
		},
		"Demo/Making": {
			"color": "orange",
			"position": 2,
		},
		"Proposal/Quotation": {
			"color": "blue",
			"position": 3,
		},
		"Negotiation": {
			"color": "yellow",
			"position": 4,
		},
		"Ready to Close": {
			"color": "purple",
			"position": 5,
		},
		"Won": {
			"color": "green",
			"position": 6,
		},
		"Lost": {
			"color": "red",
			"position": 7,
		},
	}

	for status in statuses:
		if frappe.db.exists("CRM Deal Status", status):
			continue

		doc = frappe.new_doc("CRM Deal Status")
		doc.deal_status = status
		doc.color = statuses[status]["color"]
		doc.position = statuses[status]["position"]
		doc.insert()

def add_default_communication_statuses():
	statuses = ["Open", "Replied"]

	for status in statuses:
		if frappe.db.exists("CRM Communication Status", status):
			continue

		doc = frappe.new_doc("CRM Communication Status")
		doc.status = status
		doc.insert()

def add_default_fields_layout():
	layouts = {
		"CRM Lead-Quick Entry": {
			"doctype": "CRM Lead",
			"layout": '[\n{\n"label": "Person",\n\t"fields": ["salutation", "first_name", "last_name", "email", "mobile_no", "gender"]\n},\n{\n"label": "Organization",\n\t"fields": ["organization", "website", "no_of_employees", "territory", "annual_revenue", "industry"]\n},\n{\n"label": "Other",\n"columns": 2,\n\t"fields": ["status", "lead_owner"]\n}\n]'
		},
		"CRM Deal-Quick Entry": {
			"doctype": "CRM Deal",
			"layout": '[\n{\n"label": "Select Organization",\n\t"fields": ["organization"]\n},\n{\n"label": "Organization Details",\n\t"fields": [{"label": "Organization Name", "name": "organization_name", "type": "Data"}, "website", "no_of_employees", "territory", "annual_revenue", {"label": "Industry", "name": "industry", "type": "Link", "options": "CRM Industry"}]\n},\n{\n"label": "Select Contact",\n\t"fields": [{"label": "Contact", "name": "contact", "type": "Link", "options": "Contact"}]\n},\n{\n"label": "Contact Details",\n\t"fields": [{"label": "Salutation", "name": "salutation", "type": "Link", "options": "Salutation"}, {"label": "First Name", "name": "first_name", "type": "Data"}, {"label": "Last Name", "name": "last_name", "type": "Data"}, "email", "mobile_no", {"label": "Gender", "name": "gender", "type": "Link", "options": "Gender"}]\n},\n{\n"label": "Other",\n"columns": 2,\n\t"fields": ["status", "deal_owner"]\n}\n]'
		},
		"Contact-Quick Entry": {
			"doctype": "Contact",
			"layout": '[\n{\n"label": "Salutation",\n"columns": 1,\n"fields": ["salutation"]\n},\n{\n"label": "Full Name",\n"columns": 2,\n"hideBorder": true,\n"fields": ["first_name", "last_name"]\n},\n{\n"label": "Email",\n"columns": 1,\n"hideBorder": true,\n"fields": ["email_id"]\n},\n{\n"label": "Mobile No. & Gender",\n"columns": 2,\n"hideBorder": true,\n"fields": ["mobile_no", "gender"]\n},\n{\n"label": "Organization",\n"columns": 1,\n"hideBorder": true,\n"fields": ["company_name"]\n},\n{\n"label": "Designation",\n"columns": 1,\n"hideBorder": true,\n"fields": ["designation"]\n}\n]'
		},
		"Organization-Quick Entry": {
			"doctype": "CRM Organization",
			"layout": '[\n{\n"label": "Organization Name",\n"columns": 1,\n"fields": ["organization_name"]\n},\n{\n"label": "Website & Revenue",\n"columns": 2,\n"hideBorder": true,\n"fields": ["website", "annual_revenue"]\n},\n{\n"label": "Territory",\n"columns": 1,\n"hideBorder": true,\n"fields": ["territory"]\n},\n{\n"label": "No of Employees & Industry",\n"columns": 2,\n"hideBorder": true,\n"fields": ["no_of_employees", "industry"]\n}\n]'
		},
	}

	for layout in layouts:
		if frappe.db.exists("CRM Fields Layout", layout):
			continue

		doc = frappe.new_doc("CRM Fields Layout")
		doc.type = "Quick Entry"
		doc.dt = layouts[layout]["doctype"]
		doc.layout = layouts[layout]["layout"]
		doc.insert()

def add_property_setter():
	if not frappe.db.exists("Property Setter", {"name": "Contact-main-search_fields"}):
		doc = frappe.new_doc("Property Setter")
		doc.doctype_or_field = "DocType"
		doc.doc_type = "Contact"
		doc.property = "search_fields"
		doc.property_type = "Data"
		doc.value = "email_id"
		doc.insert()

def add_email_template_custom_fields():
	if not frappe.get_meta("Email Template").has_field("enabled"):
		click.secho("* Installing Custom Fields in Email Template")

		create_custom_fields(
			{
				"Email Template": [
					{
						"default": "0",
						"fieldname": "enabled",
						"fieldtype": "Check",
						"label": "Enabled",
						"insert_after": "",
					},
					{
						"fieldname": "reference_doctype",
						"fieldtype": "Link",
						"label": "Doctype",
						"options": "DocType",
						"insert_after": "enabled",
					},
				]
			}
		)

		frappe.clear_cache(doctype="Email Template")
