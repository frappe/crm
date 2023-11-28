# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt
import json
import frappe
from frappe.model.document import Document, get_controller


class CRMListViewSettings(Document):
	pass


@frappe.whitelist()
def update(doctype, columns, rows):
	default_rows = sync_default_list_rows(doctype)

	if default_rows:
		rows = rows + default_rows

	rows = remove_duplicates(rows)

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

def remove_duplicates(l):
	return list(dict.fromkeys(l))

def sync_default_list_rows(doctype):
	list = get_controller(doctype)
	rows = []

	if hasattr(list, "default_list_data"):
		rows = list.default_list_data().get("rows")

	return rows

@frappe.whitelist()
def reset_to_default(doctype):
	if frappe.db.exists("CRM List View Settings", doctype):
		frappe.delete_doc("CRM List View Settings", doctype)