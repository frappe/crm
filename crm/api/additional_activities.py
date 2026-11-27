import frappe
from frappe.desk.form.activity import get_author_info

NOTE_FIELDS = ["title", "content", "pinned", "pinned_by", "pinned_on"]
TASK_FIELDS = ["title", "description", "status", "priority", "start_date", "due_date", "assigned_to"]


def get_note_rows(doc) -> list[dict]:
	"""Timeline rows of type "note" for a record's FCRM Notes, for a controller's get_additional_activities."""
	return get_reference_rows(doc, "note", "FCRM Note", NOTE_FIELDS)


def get_task_rows(doc) -> list[dict]:
	"""Timeline rows of type "task" for a record's CRM Tasks, for a controller's get_additional_activities."""
	return get_reference_rows(doc, "task", "CRM Task", TASK_FIELDS)


def get_reference_rows(doc, row_type: str, reference_doctype: str, fields: list[str]) -> list[dict]:
	"""Rows for the records that point at this doctype and name, if the user can read them."""
	if not frappe.has_permission(reference_doctype, "read"):
		return []
	records = frappe.get_list(
		reference_doctype,
		filters={"reference_doctype": doc.doctype, "reference_docname": doc.name},
		fields=["name", "owner", "creation", "modified", *fields],
	)
	user_info: dict = {}
	frappe.utils.add_user_info({record.owner for record in records}, user_info)
	return [
		{
			"type": row_type,
			"key": f"{row_type}:{record.name}",
			"timestamp": str(record.creation),
			"author": get_author_info(record.owner, user_info),
			"data": record,
		}
		for record in records
	]
