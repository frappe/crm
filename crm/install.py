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
			"layout": '[{"label":"Person","fields":["salutation","first_name","last_name","email","mobile_no", "gender"],"hideLabel":true},{"label":"Organization","fields":["organization","website","no_of_employees","territory","annual_revenue","industry"],"hideLabel":true,"hideBorder":false},{"label":"Other","columns":2,"fields":["status","lead_owner"],"hideLabel":true,"hideBorder":false}]'
		},
		"CRM Deal-Quick Entry": {
			"doctype": "CRM Deal",
			"layout": '[{"label": "Select Organization", "fields": ["organization"], "hideLabel": true, "editable": true}, {"label": "Organization Details", "fields": ["organization_name", "website", "no_of_employees", "territory", "annual_revenue", "industry"], "hideLabel": true, "editable": true}, {"label": "Select Contact", "fields": ["contact"], "hideLabel": true, "editable": true}, {"label": "Contact Details", "fields": ["salutation", "first_name", "last_name", "email", "mobile_no", "gender"], "hideLabel": true, "editable": true}, {"label": "Other", "columns": 2, "fields": ["status", "deal_owner"], "hideLabel": true}]'
		},
		"Contact-Quick Entry": {
			"doctype": "Contact",
			"layout": '[{"label":"Salutation","columns":1,"fields":["salutation"],"hideLabel":true},{"label":"Full Name","columns":2,"hideBorder":true,"fields":["first_name","last_name"],"hideLabel":true},{"label":"Email","columns":1,"hideBorder":true,"fields":["email_id"],"hideLabel":true},{"label":"Mobile No. & Gender","columns":2,"hideBorder":true,"fields":["mobile_no","gender"],"hideLabel":true},{"label":"Organization","columns":1,"hideBorder":true,"fields":["company_name"],"hideLabel":true},{"label":"Designation","columns":1,"hideBorder":true,"fields":["designation"],"hideLabel":true}]'
		},
		"Organization-Quick Entry": {
			"doctype": "CRM Organization",
			"layout": '[{"label":"Organization Name","columns":1,"fields":["organization_name"],"hideLabel":true},{"label":"Website & Revenue","columns":2,"hideBorder":true,"fields":["website","annual_revenue"],"hideLabel":true},{"label":"Territory","columns":1,"hideBorder":true,"fields":["territory"],"hideLabel":true},{"label":"No of Employees & Industry","columns":2,"hideBorder":true,"fields":["no_of_employees","industry"],"hideLabel":true}]'
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
