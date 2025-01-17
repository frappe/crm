import frappe


@frappe.whitelist()
def is_call_integration_enabled():
	twilio_enabled = frappe.db.get_single_value("Twilio Settings", "enabled")
	exotel_enabled = frappe.db.get_single_value("CRM Exotel Settings", "enabled")
	default_calling_medium = frappe.db.get_single_value("FCRM Settings", "default_calling_medium")

	return {
		"twilio_enabled": twilio_enabled,
		"exotel_enabled": exotel_enabled,
		"default_calling_medium": default_calling_medium,
	}


@frappe.whitelist()
def set_default_calling_medium(medium):
	return frappe.db.set_value("FCRM Settings", "FCRM Settings", "default_calling_medium", medium)


@frappe.whitelist()
def create_and_add_note_to_call_log(call_sid, content):
	"""Add note to call log based on call sid."""
	note = frappe.get_doc(
		{
			"doctype": "FCRM Note",
			"content": content,
		}
	).insert(ignore_permissions=True)

	call_log = frappe.get_doc("CRM Call Log", call_sid)
	call_log.link_with_reference_doc("FCRM Note", note.name)


@frappe.whitelist()
def create_and_add_task_to_call_log(call_sid, task):
	"""Add task to call log based on call sid."""
	_task = frappe.get_doc(
		{
			"doctype": "CRM Task",
			"title": task.get("title"),
			"description": task.get("description"),
		}
	).insert(ignore_permissions=True)

	call_log = frappe.get_doc("CRM Call Log", call_sid)
	call_log.link_with_reference_doc("CRM Task", _task.name)
