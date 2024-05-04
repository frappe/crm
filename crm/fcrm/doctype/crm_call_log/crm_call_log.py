# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class CRMCallLog(Document):
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
				"note",
				"recording_url",
				"reference_doctype",
				"reference_docname",
				"creation",
			]
			return {'columns': columns, 'rows': rows}

@frappe.whitelist()
def create_lead_from_call_log(call_log):
	lead = frappe.new_doc("CRM Lead")
	lead.first_name = "Lead from call " + call_log.get("from")
	lead.mobile_no = call_log.get("from")
	lead.lead_owner = frappe.session.user
	lead.save(ignore_permissions=True)

	frappe.db.set_value("CRM Call Log", call_log.get("name"), {
		"reference_doctype": "CRM Lead",
		"reference_docname": lead.name
	})

	if call_log.get("note"):
		frappe.db.set_value("FCRM Note", call_log.get("note"), {
			"reference_doctype": "CRM Lead",
			"reference_docname": lead.name
		})

	return lead.name