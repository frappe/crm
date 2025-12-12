# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and Contributors
# License: AGPLv3. See LICENSE

import frappe
import json


def execute():
	"""
	Add alternate_email and alternate_mobile_no fields to CRM Lead fields layouts
	"""
	
	# Update Side Panel layout
	side_panel_name = "CRM Lead-Side Panel"
	if frappe.db.exists("CRM Fields Layout", side_panel_name):
		doc = frappe.get_doc("CRM Fields Layout", side_panel_name)
		layout = json.loads(doc.layout)
		
		# Find Person section and update fields
		for section in layout:
			if section.get("name") == "person_section" or section.get("label") == "Person":
				for column in section.get("columns", []):
					if "email" in column.get("fields", []) and "alternate_email" not in column.get("fields", []):
						# Find email index and insert alternate_email after it
						fields = column.get("fields", [])
						email_index = fields.index("email")
						fields.insert(email_index + 1, "alternate_email")
					
					if "mobile_no" in column.get("fields", []) and "alternate_mobile_no" not in column.get("fields", []):
						# Find mobile_no index and insert alternate_mobile_no after it
						fields = column.get("fields", [])
						mobile_index = fields.index("mobile_no")
						fields.insert(mobile_index + 1, "alternate_mobile_no")
		
		doc.layout = json.dumps(layout)
		doc.save(ignore_permissions=True)
	
	# Update Data Fields layout
	data_fields_name = "CRM Lead-Data Fields"
	if frappe.db.exists("CRM Fields Layout", data_fields_name):
		doc = frappe.get_doc("CRM Fields Layout", data_fields_name)
		layout = json.loads(doc.layout)
		
		# Find Person section and update fields
		for section in layout:
			if section.get("name") == "person_section" or section.get("label") == "Person":
				for column in section.get("columns", []):
					fields = column.get("fields", [])
					
					# Add alternate_email after email
					if "email" in fields and "alternate_email" not in fields:
						email_index = fields.index("email")
						fields.insert(email_index + 1, "alternate_email")
					
					# Add alternate_mobile_no after mobile_no
					if "mobile_no" in fields and "alternate_mobile_no" not in fields:
						mobile_index = fields.index("mobile_no")
						fields.insert(mobile_index + 1, "alternate_mobile_no")
		
		doc.layout = json.dumps(layout)
		doc.save(ignore_permissions=True)
	
	# Update Quick Entry layout
	quick_entry_name = "CRM Lead-Quick Entry"
	if frappe.db.exists("CRM Fields Layout", quick_entry_name):
		doc = frappe.get_doc("CRM Fields Layout", quick_entry_name)
		layout = json.loads(doc.layout)
		
		# Find Person section and update fields
		for section in layout:
			if section.get("name") == "person_section":
				for column in section.get("columns", []):
					fields = column.get("fields", [])
					
					# Add alternate_email after email
					if "email" in fields and "alternate_email" not in fields:
						email_index = fields.index("email")
						fields.insert(email_index + 1, "alternate_email")
					
					# Add alternate_mobile_no after mobile_no
					if "mobile_no" in fields and "alternate_mobile_no" not in fields:
						mobile_index = fields.index("mobile_no")
						fields.insert(mobile_index + 1, "alternate_mobile_no")
		
		doc.layout = json.dumps(layout)
		doc.save(ignore_permissions=True)
	
	frappe.db.commit()

