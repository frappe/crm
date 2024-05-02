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
def get_call_log(name):
	doc = frappe.get_doc("CRM Call Log", name)
	doc = doc.as_dict()
	if doc.reference_docname and doc.reference_doctype == "CRM Lead":
		doc.lead = doc.reference_docname
		doc.lead_name = frappe.db.get_value("CRM Lead", doc.reference_docname, "lead_name")
	if doc.note:
		note = frappe.db.get_values("FCRM Note", doc.note, ["title", "content"])[0]
		doc.note_doc = {
			"name": doc.note,
			"title": note[0],
			"content": note[1]
		}

	def get_contact(number):
		c = frappe.db.get_value("Contact", {"mobile_no": number}, ["full_name", "image"], as_dict=True)
		if c:
			return [c.full_name, c.image]
		return [None, None]

	def get_lead_contact(number):
		l = frappe.db.get_value("CRM Lead", {"mobile_no": number, "converted": 0}, ["lead_name", "image"], as_dict=True)
		if l:
			return [l.lead_name, l.image]
		return [None, None]

	def get_user(user):
		u = frappe.db.get_value("User", user, ["full_name", "user_image"], as_dict=True)
		if u:
			return [u.full_name, u.user_image]
		return [None, None]

	if doc.type == "Incoming":
		doc.caller = {
			"label": get_contact(doc.get("from"))[0] or get_lead_contact(doc.get("from"))[0] or "Unknown",
			"image": get_contact(doc.get("from"))[1] or get_lead_contact(doc.get("from"))[1]
		}
		doc.receiver = {
			"label": get_user(doc.get("receiver"))[0],
			"image": get_user(doc.get("receiver"))[1]
		}
	else:
		doc.caller = {
			"label": get_user(doc.get("caller"))[0],
			"image": get_user(doc.get("caller"))[1]
		}
		doc.receiver = {
			"label": get_contact(doc.get("to"))[0] or get_lead_contact(doc.get("to"))[0] or "Unknown",
			"image": get_contact(doc.get("to"))[1] or get_lead_contact(doc.get("to"))[1]
	}

	return doc

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