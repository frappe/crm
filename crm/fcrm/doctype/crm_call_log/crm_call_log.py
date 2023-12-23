# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class CRMCallLog(Document):
		@staticmethod
		def sort_options():
			return [
				{ "label": 'Created', "value": 'creation' },
				{ "label": 'Modified', "value": 'modified' },
				{ "label": 'Status', "value": 'status' },
				{ "label": 'Type', "value": 'type' },
				{ "label": 'Duration', "value": 'duration' },
				{ "label": 'From', "value": 'from' },
				{ "label": 'To', "value": 'to' },
				{ "label": 'Caller', "value": 'caller' },
				{ "label": 'Receiver', "value": 'receiver' },
			]

		@staticmethod
		def default_list_data():
			columns = [
				{
					'label': 'From',
					'type': 'Link',
					'key': 'caller',
					'options': 'User',
					'width': '9rem',
				},
				{
					'label': 'To',
					'type': 'Link',
					'key': 'receiver',
					'options': 'User',
					'width': '9rem',
				},
				{
					'label': 'Type',
					'type': 'Select',
					'key': 'type',
					'width': '9rem',
				},
				{
					'label': 'Status',
					'type': 'Select',
					'key': 'status',
					'width': '9rem',
				},
				{
					'label': 'Duration',
					'type': 'Duration',
					'key': 'duration',
					'width': '6rem',
				},
				{
					'label': 'From (number)',
					'type': 'Data',
					'key': 'from',
					'width': '9rem',
				},
				{
					'label': 'To (number)',
					'type': 'Data',
					'key': 'to',
					'width': '9rem',
				},
				{
					'label': 'Created On',
					'type': 'Datetime',
					'key': 'creation',
					'width': '8rem',
				},
				]
			rows = [
				"name",
				"caller",
				"receiver",
				"type",
				"status",
				"duration",
				"from",
				"to",
				"creation",
			]
			return {'columns': columns, 'rows': rows}

@frappe.whitelist()
def get_call_log(name):
	doc = frappe.get_doc("CRM Call Log", name)
	_doc = doc.as_dict()
	if doc.lead:
		_doc.lead_name = frappe.db.get_value("CRM Lead", doc.lead, "lead_name")
	if doc.note:
		note = frappe.db.get_values("CRM Note", doc.note, ["title", "content"])[0]
		_doc.note_doc = {
			"name": doc.note,
			"title": note[0],
			"content": note[1]
		}

	return _doc

@frappe.whitelist()
def create_lead_from_call_log(call_log):
	lead = frappe.new_doc("CRM Lead")
	lead.first_name = "Lead from call " + call_log.get("from")
	lead.mobile_no = call_log.get("from")
	lead.lead_owner = frappe.session.user
	lead.save(ignore_permissions=True)

	frappe.db.set_value("CRM Call Log", call_log.get("name"), "lead", lead.name)

	if call_log.get("note"):
		frappe.db.set_value("CRM Note", call_log.get("note"), "lead", lead.name)

	return lead.name