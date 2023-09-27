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

	doc = frappe.db.get_values("CRM Lead", name, ["creation", "owner", "created_as_deal"])[0]
	created_as_deal = doc[2]
	is_lead = False if created_as_deal else True
	activities = [{
		"activity_type": "creation",
		"creation": doc[0],
		"owner": doc[1],
		"data": "created this " + ("deal" if created_as_deal else "lead"),
		"is_lead": is_lead,
	}]

	docinfo.versions.reverse()

	for version in docinfo.versions:
		data = json.loads(version.data)
		if not data.get("changed"):
			continue

		field_option = None

		if change := data.get("changed")[0]:
			field_label, field_option = next(((f.label, f.options) for f in lead_fields_meta if f.fieldname == change[0]), None)
			activity_type = "changed"
			if field_label == "Lead Owner" and (created_as_deal or not is_lead):
				field_label = "Deal Owner"
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
				if field_label == "Is Deal" and change[2] and is_lead:
					activity_type = "deal"
					is_lead = False
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
			"is_lead": is_lead,
			"options": field_option,
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
			"is_lead": is_lead,
		}
		activities.append(activity)

	activities.sort(key=lambda x: x["creation"], reverse=True)
	activities = handle_multiple_versions(activities)

	return activities

def handle_multiple_versions(versions):
	activities = []
	grouped_versions = []
	old_version = None
	for version in versions:
		is_version = version["activity_type"] in ["changed", "added", "removed"]
		if not is_version:
			activities.append(version)
		if not old_version:
			old_version = version
			if is_version: grouped_versions.append(version)
			continue
		if is_version and old_version.get("owner") and version["owner"] == old_version["owner"]:
			grouped_versions.append(version)
		else:
			if grouped_versions:
				activities.append(parse_grouped_versions(grouped_versions))
			grouped_versions = []
			if is_version: grouped_versions.append(version)
		old_version = version
		if version == versions[-1] and grouped_versions:
			activities.append(parse_grouped_versions(grouped_versions))

	return activities

def parse_grouped_versions(versions):
	version = versions[0]
	if len(versions) == 1:
		return version
	other_versions = versions[1:]
	version["other_versions"] = other_versions
	return version