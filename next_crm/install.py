# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt
from __future__ import unicode_literals
import click
import frappe

from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

def before_install():
	pass

def after_install(force=False):
	add_default_lead_statuses()
	add_default_deal_statuses()
	add_default_communication_statuses()
	add_default_fields_layout(force)
	add_property_setter()
	add_email_template_custom_fields()
	add_todo_custom_title_field()
	erpnext_crm_settings = frappe.get_single("ERPNext CRM Settings")
	erpnext_crm_settings.enabled = True
	erpnext_crm_settings.save()
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
		"Open": {
			"color": "gray",
			"position": 1,
		},
		"Qualification": {
			"color": "gray",
			"position": 2,
		},
		"Demo/Making": {
			"color": "orange",
			"position": 3,
		},
		"Proposal/Quotation": {
			"color": "blue",
			"position": 4,
		},
		"Negotiation": {
			"color": "yellow",
			"position": 5,
		},
		"Ready to Close": {
			"color": "purple",
			"position": 6,
		},
		"Won": {
			"color": "green",
			"position": 7,
		},
		"Lost": {
			"color": "red",
			"position": 8,
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

def add_default_fields_layout(force=False):
	quick_entry_layouts = {
		"Lead-Quick Entry": {
			"doctype": "Lead",
			"layout": '[{"label":"Person","fields":["salutation","first_name","last_name","email_id","mobile_no", "gender"],"hideLabel":true},{"label":"Customer","fields":["company_name","website","no_of_employees","territory","annual_revenue","industry"],"hideLabel":true,"hideBorder":false},{"label":"Other","columns":2,"fields":["status","lead_owner"],"hideLabel":true,"hideBorder":false}]'
		},
		"Opportunity-Quick Entry": {
			"doctype": "Opportunity",
			"layout": '[{"label": "Select Customer", "fields": ["customer"], "hideLabel": true, "editable": true}, {"label": "Customer Details", "fields": ["customer_name", "website", "no_of_employees", "territory", "opportunity_amount", "industry"], "hideLabel": true, "editable": true}, {"label": "Select Contact", "fields": ["contact_person"], "hideLabel": true, "editable": true}, {"label": "Other", "columns": 3, "fields": ["status", "opportunity_owner", "lead"], "hideLabel": true}]'
		},
		"Contact-Quick Entry": {
			"doctype": "Contact",
			"layout": '[{"label":"Salutation","columns":1,"fields":["salutation"],"hideLabel":true},{"label":"Full Name","columns":2,"hideBorder":true,"fields":["first_name","last_name"],"hideLabel":true},{"label":"Email","columns":1,"hideBorder":true,"fields":["email_id"],"hideLabel":true},{"label":"Mobile No. & Gender","columns":2,"hideBorder":true,"fields":["mobile_no","gender"],"hideLabel":true},{"label":"Customer","columns":1,"hideBorder":true,"fields":["company_name"],"hideLabel":true},{"label":"Designation","columns":1,"hideBorder":true,"fields":["designation"],"hideLabel":true},{"label":"Address","columns":1,"hideBorder":true,"fields":["address"],"hideLabel":true}]'
		},
		"Customer-Quick Entry": {
			"doctype": "Customer",
			"layout": '[{"label":"Customer Name","columns":1,"fields":["customer_name"],"hideLabel":true},{"label":"Website & Revenue","columns":2,"hideBorder":true,"fields":["website","annual_revenue"],"hideLabel":true},{"label":"Territory","columns":1,"hideBorder":true,"fields":["territory"],"hideLabel":true},{"label":"No of Employees & Industry","columns":2,"hideBorder":true,"fields":["no_of_employees","industry"],"hideLabel":true},{"label":"Address","columns":1,"hideBorder":true,"fields":["customer_primary_address"],"hideLabel":true}]'
		},
		"Address-Quick Entry": {
			"doctype": "Address",
			"layout": '[{"label":"Address","columns":1,"fields":["address_title","address_type","address_line1","address_line2","city","state","country","pincode"],"hideLabel":true}]'
		},
	}

	sidebar_fields_layouts = {
		"Lead-Side Panel": {
			"doctype": "Lead",
			"layout": '[{"label": "Details", "name": "details", "opened": true, "fields": ["customer", "website", "territory", "industry", "job_title", "source", "lead_owner"]}, {"label": "Person", "name": "person_tab", "opened": true, "fields": ["salutation", "first_name", "last_name", "email_id", "mobile_no"]}]'
		},
		"Opportunity-Side Panel": {
			"doctype": "Opportunity",
			"layout": '[{"label":"Contacts","name":"contacts_section","opened":true,"editable":false,"contacts":[]},{"label":"Customer Details","name":"customer_tab","opened":true,"fields":["customer","website","territory","opportunity_amount","transaction_date","probability","opportunity_owner"]}]'
		},
		"Contact-Side Panel": {
			"doctype": "Contact",
			"layout": '[{"label":"Details","name":"details","opened":true,"fields":["salutation","first_name","last_name","email_id","mobile_no","gender","company_name","designation","address"]}]'
		},
		"Customer-Side Panel": {
			"doctype": "Customer",
			"layout": '[{"label":"Details","name":"details","opened":true,"fields":["customer_name","website","territory","industry","no_of_employees","customer_primary_address"]}]'
		},
	}

	for layout in quick_entry_layouts:
		if frappe.db.exists("CRM Fields Layout", layout):
			if force:
				frappe.delete_doc("CRM Fields Layout", layout)
			else:
				continue

		doc = frappe.new_doc("CRM Fields Layout")
		doc.type = "Quick Entry"
		doc.dt = quick_entry_layouts[layout]["doctype"]
		doc.layout = quick_entry_layouts[layout]["layout"]
		doc.insert()

	for layout in sidebar_fields_layouts:
		if frappe.db.exists("CRM Fields Layout", layout):
			if force:
				frappe.delete_doc("CRM Fields Layout", layout)
			else:
				continue

		doc = frappe.new_doc("CRM Fields Layout")
		doc.type = "Side Panel"
		doc.dt = sidebar_fields_layouts[layout]["doctype"]
		doc.layout = sidebar_fields_layouts[layout]["layout"]
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

def add_todo_custom_title_field():
	if not frappe.db.exists("Custom Field", {"label": "Title"}) or frappe.db.exists(
		"DocField", {"label": "Title"}
	):
		custom_fields = {
			"ToDo": [
				{
					"fieldname": "custom_title",
					"fieldtype": "Data",
					"label": "Title",
					"insert_after": "description_and_status",
				}
			],
		}
		create_custom_fields(custom_fields, ignore_validate=True)

