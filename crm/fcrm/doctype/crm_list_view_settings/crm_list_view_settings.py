# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt
import json
import frappe
from frappe.model.document import Document


class CRMListViewSettings(Document):
	pass


@frappe.whitelist()
def update(doctype, columns, rows):
	if not frappe.db.exists("CRM List View Settings", doctype):
		# create new CRM List View Settings
		doc = frappe.new_doc("CRM List View Settings")
		doc.name = doctype
		doc.columns = json.dumps(columns)
		doc.rows = json.dumps(rows)
		doc.insert()
	else:
		# update existing CRM List View Settings
		doc = frappe.get_doc("CRM List View Settings", doctype)
		doc.columns = json.dumps(columns)
		doc.rows = json.dumps(rows)
		doc.save()
