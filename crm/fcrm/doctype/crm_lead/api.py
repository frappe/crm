import json

import frappe
from frappe import _
from frappe.desk.form.load import get_docinfo


@frappe.whitelist()
def get_lead(name):
	Lead = frappe.qb.DocType("CRM Lead")

	query = (
		frappe.qb.from_(Lead)
		.select("*")
		.where(Lead.name == name)
		.limit(1)
	)

	lead = query.run(as_dict=True)
	if not len(lead):
		frappe.throw(_("Lead not found"), frappe.DoesNotExistError)
	lead = lead.pop()

	return lead

@frappe.whitelist()
def get_activities(name):
	get_docinfo('', "CRM Lead", name)
	docinfo = frappe.response["docinfo"]
	lead_fields_meta = frappe.get_meta("CRM Lead").fields

	doc = frappe.get_doc("CRM Lead", name, fields=["creation", "owner"])
	activities = [{
		"activity_type": "creation",
		"creation": doc.creation,
		"owner": doc.owner,
		"data": "created this lead",
	}]

	for version in docinfo.versions:
		data = json.loads(version.data)
		if not data.get("changed"):
			continue
		if change := data.get("changed")[0]:
			activity_type = "changed"
			field_label = next((f.label for f in lead_fields_meta if f.fieldname == change[0]), None)
			data = {
				"field": change[0],
				"field_label": field_label,
				"old_value": change[1],
				"value": change[2],
			}
			if not change[1] and not change[2]:
				continue
			if not change[1] and change[2]:
				activity_type = "added"
				data = {
					"field": change[0],
					"field_label": field_label,
					"value": change[2],
				}
			elif change[1] and not change[2]:
				activity_type = "removed"
				data = {
					"field": change[0],
					"field_label": field_label,
					"value": change[1],
				}

		activity = {
			"activity_type": activity_type,
			"creation": version.creation,
			"owner": version.owner,
			"data": data,
		}
		activities.append(activity)

	for communication in docinfo.communications:
		activity = {
			"activity_type": "communication",
			"creation": communication.creation,
			"data": {
				"subject": communication.subject,
				"content": communication.content,
				"sender_full_name": communication.sender_full_name,
				"sender": communication.sender,
				"recipients": communication.recipients,
				"cc": communication.cc,
				"bcc": communication.bcc,
				"read_by_recipient": communication.read_by_recipient,
			},
		}
		activities.append(activity)

	activities.sort(key=lambda x: x["creation"], reverse=True)

	return activities