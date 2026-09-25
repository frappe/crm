import json

import frappe
from bs4 import BeautifulSoup
from frappe import _
from frappe.desk.form.load import get_docinfo
from frappe.query_builder import JoinType
from frappe.translate import get_translated_doctypes

from crm.fcrm.doctype.crm_call_log.crm_call_log import parse_call_log
from crm.fcrm.doctype.crm_fields_layout.crm_fields_layout import get_permlevel_access


@frappe.whitelist()
def get_activities(name: str):
	if frappe.db.exists("CRM Deal", name):
		return get_deal_activities(name)
	elif frappe.db.exists("CRM Lead", name):
		return get_lead_activities(name)
	else:
		frappe.throw(_("Document not found"), frappe.DoesNotExistError)


def get_deal_activities(name: str):
	if not frappe.has_permission("CRM Deal", "read", name):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	get_docinfo("", "CRM Deal", name)
	docinfo = frappe.response["docinfo"]
	deal_fields = get_readable_fields("CRM Deal")
	avoid_fields = [
		"lead",
		"response_by",
		"sla_creation",
		"sla",
		"sla_status",
		"first_response_time",
		"first_responded_on",
		"last_response_time",
		"last_responded_on",
	]

	doc = frappe.db.get_values("CRM Deal", name, ["creation", "owner", "lead", "currency"])[0]
	lead = doc[2]

	activities = []
	calls = []
	notes = []
	tasks = []
	attachments = []
	creation_text = _("created this deal")

	if lead:
		creation_text = _("converted the lead to this deal")
		# a user can have access to the deal but not the lead it came from, so
		# skip the lead's history instead of failing the whole timeline
		if frappe.has_permission("CRM Lead", "read", lead):
			# ungrouped, so the merged lead + deal timeline is grouped only once below
			activities, calls, notes, tasks, attachments = get_lead_activities(lead, group=False)

	activities.append(
		{
			"activity_type": "creation",
			"creation": doc[0],
			"owner": doc[1],
			"data": creation_text,
			"is_lead": False,
		}
	)

	docinfo.versions.reverse()

	deal = frappe._dict(doctype="CRM Deal", name=name, currency=doc[3])
	activities += _version_activities(docinfo.versions, deal_fields, avoid_fields, is_lead=False, doc=deal)

	for comment in docinfo.comments:
		activity = {
			"name": comment.name,
			"activity_type": "comment",
			"creation": comment.creation,
			"owner": comment.owner,
			"content": comment.content,
			"attachments": get_attachments("Comment", comment.name),
			"is_lead": False,
		}
		activities.append(activity)

	for communication in docinfo.communications + docinfo.automated_messages:
		activity = {
			"name": communication.name,
			"activity_type": "communication",
			"communication_type": communication.communication_type,
			"communication_date": communication.communication_date or communication.creation,
			"creation": communication.creation,
			"data": {
				"subject": communication.subject,
				"content": communication.content,
				"sender_full_name": communication.sender_full_name,
				"sender": communication.sender,
				"recipients": communication.recipients,
				"cc": communication.cc,
				"bcc": communication.bcc,
				"attachments": get_attachments("Communication", communication.name),
				"read_by_recipient": communication.read_by_recipient,
				"delivery_status": communication.delivery_status,
			},
			"is_lead": False,
		}
		activities.append(activity)

	for attachment_log in docinfo.attachment_logs:
		activity = {
			"name": attachment_log.name,
			"activity_type": "attachment_log",
			"creation": attachment_log.creation,
			"owner": attachment_log.owner,
			"data": parse_attachment_log(attachment_log.content, attachment_log.comment_type),
			"is_lead": False,
		}
		activities.append(activity)

	linked = get_linked_calls(name)
	calls = calls + linked.get("calls", [])
	notes = notes + get_linked_notes(name) + linked.get("notes", [])
	tasks = tasks + get_linked_tasks(name) + linked.get("tasks", [])
	attachments = attachments + get_attachments("CRM Deal", name)

	activities.sort(key=lambda x: x["creation"], reverse=True)
	activities = handle_multiple_versions(activities)
	frappe.response.pop("docinfo", None)

	return activities, calls, notes, tasks, attachments


def get_lead_activities(name: str, group: bool = True):
	if not frappe.has_permission("CRM Lead", "read", name):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	get_docinfo("", "CRM Lead", name)
	docinfo = frappe.response["docinfo"]
	lead_fields = get_readable_fields("CRM Lead")
	avoid_fields = [
		"converted",
		# rebuilt from salutation / first / middle / last name on every save
		"lead_name",
		"response_by",
		"sla_creation",
		"sla",
		"sla_status",
		"first_response_time",
		"first_responded_on",
		"last_response_time",
		"last_responded_on",
	]

	doc = frappe.db.get_values("CRM Lead", name, ["creation", "owner"])[0]
	activities = [
		{
			"activity_type": "creation",
			"creation": doc[0],
			"owner": doc[1],
			"data": _("created this lead"),
			"is_lead": True,
		}
	]

	docinfo.versions.reverse()

	lead = frappe._dict(doctype="CRM Lead", name=name)
	activities += _version_activities(docinfo.versions, lead_fields, avoid_fields, is_lead=True, doc=lead)

	for comment in docinfo.comments:
		activity = {
			"name": comment.name,
			"activity_type": "comment",
			"creation": comment.creation,
			"owner": comment.owner,
			"content": comment.content,
			"attachments": get_attachments("Comment", comment.name),
			"is_lead": True,
		}
		activities.append(activity)

	for communication in docinfo.communications + docinfo.automated_messages:
		activity = {
			"name": communication.name,
			"activity_type": "communication",
			"communication_type": communication.communication_type,
			"communication_date": communication.communication_date or communication.creation,
			"creation": communication.creation,
			"data": {
				"subject": communication.subject,
				"content": communication.content,
				"sender_full_name": communication.sender_full_name,
				"sender": communication.sender,
				"recipients": communication.recipients,
				"cc": communication.cc,
				"bcc": communication.bcc,
				"attachments": get_attachments("Communication", communication.name),
				"read_by_recipient": communication.read_by_recipient,
				"delivery_status": communication.delivery_status,
			},
			"is_lead": True,
		}
		activities.append(activity)

	for attachment_log in docinfo.attachment_logs:
		activity = {
			"name": attachment_log.name,
			"activity_type": "attachment_log",
			"creation": attachment_log.creation,
			"owner": attachment_log.owner,
			"data": parse_attachment_log(attachment_log.content, attachment_log.comment_type),
			"is_lead": True,
		}
		activities.append(activity)

	linked = get_linked_calls(name)
	calls = linked.get("calls", [])
	notes = get_linked_notes(name) + linked.get("notes", [])
	tasks = get_linked_tasks(name) + linked.get("tasks", [])
	attachments = get_attachments("CRM Lead", name)

	activities.sort(key=lambda x: x["creation"], reverse=True)
	if group:
		activities = handle_multiple_versions(activities)
	frappe.response.pop("docinfo", None)

	return activities, calls, notes, tasks, attachments


def get_readable_fields(doctype: str):
	"""Map of fieldname to label & options, skipping fields the user cannot read.

	Permlevel restrictions already hide these fields on the form layout, so the
	activity timeline has to hide them too instead of leaking their values.
	"""
	allowed_permlevels = get_permlevel_access("read", doctype)

	return {
		field.fieldname: {"label": field.label, "options": field.options, "df": field}
		for field in frappe.get_meta(doctype).fields
		if field.permlevel == 0 or field.permlevel in allowed_permlevels
	}


def get_attachments(doctype: str, name: str):
	return (
		frappe.db.get_all(
			"File",
			filters={"attached_to_doctype": doctype, "attached_to_name": name},
			fields=[
				"name",
				"file_name",
				"file_type",
				"file_url",
				"file_size",
				"is_private",
				"modified",
				"creation",
				"owner",
			],
		)
		or []
	)


def _version_activities(
	versions: list, fields: dict, avoid_fields: list, is_lead: bool, doc: dict | None = None
) -> list:
	"""Convert a docinfo versions list into activity dicts, one per changed field.

	Fields absent from *fields* (permlevel-restricted or outside the doctype) are
	silently skipped, as are entries in *avoid_fields* and no-op changes where
	both sides are blank (None, "" or 0). A value going to 0 is still a change.
	"""
	translated_doctypes = set(get_translated_doctypes())
	result = []
	for version in versions:
		version_data = json.loads(version.data)
		for fieldname, old_value, new_value in version_data.get("changed") or []:
			field = fields.get(fieldname)
			if not field or fieldname in avoid_fields:
				continue
			# numeric fields flip between 0 and None on plain saves; that is not a change
			if is_blank(old_value) and is_blank(new_value):
				continue

			# Frappe stores numbers formatted ("₹ 1,000.00") but leaves 0 raw; match them
			old_value = format_zero(old_value, field.get("df"), doc)
			new_value = format_zero(new_value, field.get("df"), doc)

			field_label = field.get("label") or fieldname
			field_option = field.get("options") or None

			activity_type = "changed"
			activity_data = {
				"field": fieldname,
				"field_label": field_label,
				"old_value": old_value,
				"value": new_value,
			}

			if is_empty(old_value):
				activity_type = "added"
				activity_data = {"field": fieldname, "field_label": field_label, "value": new_value}
			elif is_empty(new_value):
				activity_type = "removed"
				activity_data = {"field": fieldname, "field_label": field_label, "value": old_value}

			if field_option in translated_doctypes:
				activity_data["value"] = _(activity_data["value"])
				if not is_empty(activity_data.get("old_value")):
					activity_data["old_value"] = _(activity_data["old_value"])

			result.append(
				{
					"activity_type": activity_type,
					"creation": version.creation,
					"owner": version.owner,
					"data": activity_data,
					"is_lead": is_lead,
					"options": field_option,
				}
			)
	return result


def is_empty(value) -> bool:
	return value is None or value == ""


def is_blank(value) -> bool:
	return is_empty(value) or value == 0


NUMBER_FIELDTYPES = ("Currency", "Int", "Long Int", "Float", "Percent")


def format_zero(value, df, doc=None):
	if value == 0 and not isinstance(value, bool) and df and df.fieldtype in NUMBER_FIELDTYPES:
		return frappe.format_value(value, df, doc)
	return value


def handle_multiple_versions(activities: list):
	"""Group the field changes of each save into one timeline entry.

	Entries from one save share owner and creation; the first becomes the head
	and the rest go in its ``other_versions``. Expects *activities* sorted by
	creation and not grouped yet, so groups never nest.
	"""
	result = []
	group = []
	for activity in activities:
		if activity["activity_type"] not in ("changed", "added", "removed"):
			if group:
				result.append(parse_grouped_versions(group))
				group = []
			result.append(activity)
			continue

		if group and not is_same_save(group[0], activity):
			result.append(parse_grouped_versions(group))
			group = []
		group.append(activity)

	if group:
		result.append(parse_grouped_versions(group))

	return result


def is_same_save(a: dict, b: dict) -> bool:
	return bool(a.get("owner")) and a.get("owner") == b.get("owner") and a["creation"] == b["creation"]


def parse_grouped_versions(versions: list):
	version = versions[0]
	if len(versions) > 1:
		version["other_versions"] = versions[1:]
	return version


def get_linked_calls(name: str):
	calls = frappe.db.get_all(
		"CRM Call Log",
		filters={"reference_docname": name},
		fields=[
			"name",
			"caller",
			"receiver",
			"from",
			"to",
			"duration",
			"start_time",
			"end_time",
			"status",
			"type",
			"recording_url",
			"creation",
			"note",
		],
	)

	linked_calls = frappe.db.get_all(
		"Dynamic Link", filters={"link_name": name, "parenttype": "CRM Call Log"}, pluck="parent"
	)

	notes = []
	tasks = []

	if linked_calls:
		CallLog = frappe.qb.DocType("CRM Call Log")
		Link = frappe.qb.DocType("Dynamic Link")
		query = (
			frappe.qb.from_(CallLog)
			.select(
				CallLog.name,
				CallLog.caller,
				CallLog.receiver,
				CallLog["from"],
				CallLog.to,
				CallLog.duration,
				CallLog.start_time,
				CallLog.end_time,
				CallLog.status,
				CallLog.type,
				CallLog.recording_url,
				CallLog.creation,
				CallLog.note,
				Link.link_doctype,
				Link.link_name,
			)
			.join(Link, JoinType.inner)
			.on(Link.parent == CallLog.name)
			.where(CallLog.name.isin(linked_calls))
		)
		_calls = query.run(as_dict=True)

		for call in _calls:
			if call.get("link_doctype") == "FCRM Note":
				notes.append(call.link_name)
			elif call.get("link_doctype") == "CRM Task":
				tasks.append(call.link_name)

		_calls = [call for call in _calls if call.get("link_doctype") not in ["FCRM Note", "CRM Task"]]
		if _calls:
			calls = calls + _calls

	if notes:
		notes = frappe.db.get_all(
			"FCRM Note",
			filters={"name": ("in", notes)},
			fields=["name", "title", "content", "owner", "modified"],
		)

	if tasks:
		tasks = frappe.db.get_all(
			"CRM Task",
			filters={"name": ("in", tasks)},
			fields=[
				"name",
				"title",
				"description",
				"assigned_to",
				"due_date",
				"priority",
				"status",
				"modified",
			],
		)

	calls = [parse_call_log(call) for call in calls] if calls else []

	return {"calls": calls, "notes": notes, "tasks": tasks}


def get_linked_notes(name: str):
	notes = frappe.db.get_all(
		"FCRM Note",
		filters={"reference_docname": name},
		fields=["name", "title", "content", "owner", "modified", "creation"],
	)
	return notes or []


def get_linked_tasks(name: str):
	tasks = frappe.db.get_all(
		"CRM Task",
		filters={"reference_docname": name},
		fields=[
			"name",
			"title",
			"description",
			"assigned_to",
			"due_date",
			"priority",
			"status",
			"modified",
			"creation",
		],
	)
	return tasks or []


def parse_attachment_log(html: str, type: str):
	soup = BeautifulSoup(html, "html.parser")
	a_tag = soup.find("a")
	type = "added" if type == "Attachment" else "removed"
	if not a_tag:
		return {
			"type": type,
			"file_name": html.replace("Removed ", ""),
			"file_url": "",
			"is_private": False,
		}

	is_private = False
	if "private/files" in a_tag["href"]:
		is_private = True

	return {
		"type": type,
		"file_name": a_tag.text,
		"file_url": a_tag["href"],
		"is_private": is_private,
	}
