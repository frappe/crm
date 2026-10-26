import json

import frappe
from bs4 import BeautifulSoup
from frappe import _
from frappe.desk.form.load import get_docinfo
from frappe.query_builder import JoinType
from frappe.translate import get_translated_doctypes

from crm.api.merge import MERGE_CONFIG
from crm.fcrm.doctype.crm_call_log.crm_call_log import parse_call_log
from crm.fcrm.doctype.crm_fields_layout.crm_fields_layout import get_permlevel_access


@frappe.whitelist()
def get_activities(name: str):
	"""Return the timeline of a Lead or Deal: field changes, emails, comments, calls, notes, tasks and attachments."""
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
		"first_response_time",
		"first_responded_on",
	]

	doc = frappe.db.get_values("CRM Deal", name, ["creation", "owner", "lead"])[0]
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
			activities, calls, notes, tasks, attachments = get_lead_activities(lead)
			activities = ungroup_note_activities(activities)

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

	for version in docinfo.versions:
		data = json.loads(version.data)
		if not data.get("changed"):
			continue

		if change := data.get("changed")[0]:
			field = deal_fields.get(change[0], None)

			if not field or change[0] in avoid_fields or (not change[1] and not change[2]):
				continue

			field_label = field.get("label") or change[0]
			field_option = field.get("options") or None

			activity_type = "changed"
			data = {
				"field": change[0],
				"field_label": field_label,
				"old_value": change[1],
				"value": change[2],
			}

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

			if data.get("value") and field_option and is_translatable(field_option):
				data["value"] = _(data["value"])

				if data.get("old_value"):
					data["old_value"] = _(data["old_value"])

		activity = {
			"activity_type": activity_type,
			"creation": version.creation,
			"owner": version.owner,
			"data": data,
			"is_lead": False,
			"options": field_option,
		}
		activities.append(activity)

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

	linked_calls = get_linked_calls(name)
	calls = calls + linked_calls.get("calls", [])
	# the lead's note events already came with its activities, so only add the deal's own
	lead_notes = {n.get("name") for n in notes}
	deal_notes = [
		n for n in get_linked_notes(name) + linked_calls.get("notes", []) if n.get("name") not in lead_notes
	]
	notes = notes + deal_notes
	tasks = tasks + get_linked_tasks(name) + linked_calls.get("tasks", [])
	attachments = attachments + get_attachments("CRM Deal", name)
	activities += get_note_activities(deal_notes, is_lead=False)

	activities.sort(key=lambda x: x["creation"], reverse=True)
	activities = handle_multiple_versions(activities)
	activities = group_note_activities(activities)

	return activities, calls, notes, tasks, attachments


def get_lead_activities(name: str):
	if not frappe.has_permission("CRM Lead", "read", name):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	get_docinfo("", "CRM Lead", name)
	docinfo = frappe.response["docinfo"]
	lead_fields = get_readable_fields("CRM Lead")
	avoid_fields = [
		"converted",
		"response_by",
		"sla_creation",
		"sla",
		"first_response_time",
		"first_responded_on",
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

	merge_activities, merge_versions = get_merge_activities(name, lead_fields)
	activities += merge_activities

	docinfo.versions.reverse()

	for version in docinfo.versions:
		if version.name in merge_versions:
			continue
		data = json.loads(version.data)
		if not data.get("changed"):
			continue

		if change := data.get("changed")[0]:
			field = lead_fields.get(change[0], None)

			if not field or change[0] in avoid_fields or (not change[1] and not change[2]):
				continue

			field_label = field.get("label") or change[0]
			field_option = field.get("options") or None

			activity_type = "changed"
			data = {
				"field": change[0],
				"field_label": field_label,
				"old_value": change[1],
				"value": change[2],
			}

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

			if data.get("value") and field_option and is_translatable(field_option):
				data["value"] = _(data["value"])

				if data.get("old_value"):
					data["old_value"] = _(data["old_value"])

		activity = {
			"activity_type": activity_type,
			"creation": version.creation,
			"owner": version.owner,
			"data": data,
			"is_lead": True,
			"options": field_option,
		}
		activities.append(activity)

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

	linked_calls = get_linked_calls(name)
	calls = linked_calls.get("calls", [])
	notes = get_linked_notes(name) + linked_calls.get("notes", [])
	tasks = get_linked_tasks(name) + linked_calls.get("tasks", [])
	attachments = get_attachments("CRM Lead", name)
	activities += get_note_activities(notes, is_lead=True)

	activities.sort(key=lambda x: x["creation"], reverse=True)
	activities = handle_multiple_versions(activities)
	activities = group_note_activities(activities)

	return activities, calls, notes, tasks, attachments


def get_merge_activities(name: str, lead_fields: dict) -> tuple[list, set]:
	"""Merge and split entries for a lead, from either side of its CRM Merge Logs, and the
	Versions those merges and splits saved on the target, which the feed shows inside the entry
	rather than as field changes of their own."""
	logs = frappe.get_all(
		"CRM Merge Log",
		filters={"reference_doctype": "CRM Lead"},
		or_filters={"target_document_name": name, "source_document_name": name},
		fields=[
			"target_document_name",
			"source_document_name",
			"merged_by",
			"merged_at",
			"merge_version",
			"split_by",
			"split_at",
			"split_version",
		],
	)
	if not logs:
		return [], set()

	others = {
		log.source_document_name if log.target_document_name == name else log.target_document_name
		for log in logs
	}
	# get_list, so a lead the user cannot read shows as its ID only
	titles = dict(
		frappe.get_list(
			"CRM Lead", filters={"name": ("in", list(others))}, fields=["name", "lead_name"], as_list=True
		)
	)
	version_names = {v for log in logs for v in (log.merge_version, log.split_version) if v}
	versions = dict(
		frappe.get_all(
			"Version", filters={"name": ("in", list(version_names))}, fields=["name", "data"], as_list=True
		)
	)
	denylist = MERGE_CONFIG["CRM Lead"]["denylist"]

	def changed_fields(version_name):
		changed = json.loads(versions.get(version_name) or "{}").get("changed") or []
		return [
			(lead_fields[field]["label"] or field, bool(old_value))
			for field, old_value, _new_value in changed
			if field in lead_fields and field not in denylist
		]

	activities = []
	for log in logs:
		is_target = log.target_document_name == name
		other = log.source_document_name if is_target else log.target_document_name
		data = {"lead": other, "lead_title": titles.get(other), "is_target": is_target}

		merge_data = {**data, "filled": [], "replaced": []}
		if is_target:
			for label, had_value in changed_fields(log.merge_version):
				merge_data["replaced" if had_value else "filled"].append(label)
		activities.append(
			{
				"activity_type": "merge",
				"creation": log.merged_at,
				"owner": log.merged_by,
				"data": merge_data,
				"is_lead": True,
			}
		)

		if log.split_at:
			restored = [label for label, _ in changed_fields(log.split_version)] if is_target else []
			activities.append(
				{
					"activity_type": "split",
					"creation": log.split_at,
					"owner": log.split_by,
					"data": {**data, "restored": restored},
					"is_lead": True,
				}
			)

	return activities, version_names


def get_readable_fields(doctype: str):
	"""Map of fieldname to label & options, skipping fields the user cannot read.

	Permlevel restrictions already hide these fields on the form layout, so the
	activity timeline has to hide them too instead of leaking their values.
	"""
	allowed_permlevels = get_permlevel_access("read", doctype)

	return {
		field.fieldname: {"label": field.label, "options": field.options}
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


def handle_multiple_versions(versions: list):
	activities = []
	grouped_versions = []
	old_version = None
	for version in versions:
		is_version = version["activity_type"] in ["changed", "added", "removed"]
		if not is_version:
			activities.append(version)
		if not old_version:
			old_version = version
			if is_version:
				grouped_versions.append(version)
			continue
		if is_version and old_version.get("owner") and version["owner"] == old_version["owner"]:
			grouped_versions.append(version)
		else:
			if grouped_versions:
				activities.append(parse_grouped_versions(grouped_versions))
			grouped_versions = []
			if is_version:
				grouped_versions.append(version)
		old_version = version
		if version == versions[-1] and grouped_versions:
			activities.append(parse_grouped_versions(grouped_versions))

	return activities


def group_note_activities(activities: list):
	"""Fold back-to-back note entries by the same person into one, like field changes."""
	grouped = []
	for activity in activities:
		previous = grouped[-1] if grouped else None
		if (
			activity["activity_type"] == "note"
			and previous
			and previous["activity_type"] == "note"
			and previous["owner"] == activity["owner"]
		):
			previous.setdefault("other_notes", []).append(activity)
		else:
			grouped.append(activity)
	return grouped


def ungroup_note_activities(activities: list):
	"""Undo `group_note_activities` so the lead's notes can regroup with the deal's."""
	ungrouped = []
	for activity in activities:
		ungrouped.append(activity)
		ungrouped.extend(activity.pop("other_notes", []))
	return ungrouped


def parse_grouped_versions(versions: list):
	version = versions[0]
	if len(versions) == 1:
		return version
	other_versions = versions[1:]
	version["other_versions"] = other_versions
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
			"reference_doctype",
			"reference_docname",
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
				CallLog.reference_doctype,
				CallLog.reference_docname,
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
			fields=[
				"name",
				"title",
				"content",
				"pinned",
				"pinned_by",
				"pinned_on",
				"owner",
				"modified",
				"creation",
			],
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
		fields=[
			"name",
			"title",
			"content",
			"pinned",
			"pinned_by",
			"pinned_on",
			"owner",
			"modified",
			"creation",
		],
	)
	return notes or []


def get_note_activities(notes: list, is_lead: bool):
	"""Timeline entries for notes being added, pinned and unpinned."""
	notes = [n for n in notes if n.get("name")]
	if not notes:
		return []

	titles = {n.get("name"): n.get("title") for n in notes}
	activities = [
		{
			"name": note.get("name"),
			"activity_type": "note",
			"creation": note.get("creation"),
			"owner": note.get("owner"),
			"data": {"action": "added", "note": note.get("name"), "title": note.get("title")},
			"is_lead": is_lead,
		}
		for note in notes
	]

	versions = frappe.get_all(
		"Version",
		filters={"ref_doctype": "FCRM Note", "docname": ["in", list(titles)], "data": ["like", '%"pinned"%']},
		fields=["name", "docname", "owner", "creation", "data"],
	)
	for version in versions:
		changed = json.loads(version.data).get("changed", [])
		pinned = next((c[2] for c in changed if c[0] == "pinned"), None)
		if pinned is None:
			continue
		activities.append(
			{
				"name": version.name,
				"activity_type": "note",
				"creation": version.creation,
				"owner": version.owner,
				"data": {
					"action": "pinned" if int(pinned) else "unpinned",
					"note": version.docname,
					"title": titles.get(version.docname),
				},
				"is_lead": is_lead,
			}
		)
	return activities


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


def is_translatable(doctype: str) -> bool:
	return doctype in get_translated_doctypes()
