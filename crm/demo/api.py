import json

import frappe

DEMO_STATE_KEY = "crm_demo_data_created"
DEMO_LEADS_KEY = "crm_demo_leads"
DEMO_NOTES_KEY = "crm_demo_notes"
DEMO_TASKS_KEY = "crm_demo_tasks"


def create_demo_data():
	if frappe.db.get_default(DEMO_STATE_KEY):
		return

	from crm.demo.leads import create_demo_leads
	from crm.demo.notes import create_demo_notes
	from crm.demo.tasks import create_demo_tasks
	from crm.demo.users import create_demo_users

	demo_users = create_demo_users()
	lead_names = create_demo_leads(demo_users)
	note_names = create_demo_notes(lead_names)
	task_names = create_demo_tasks(lead_names, demo_users)
	frappe.db.set_default(DEMO_LEADS_KEY, json.dumps(lead_names))
	frappe.db.set_default(DEMO_NOTES_KEY, json.dumps(note_names))
	frappe.db.set_default(DEMO_TASKS_KEY, json.dumps(task_names))
	frappe.db.set_default(DEMO_STATE_KEY, "1")


@frappe.whitelist()
def clear_demo_data():
	if not frappe.db.get_default(DEMO_STATE_KEY):
		return

	from crm.demo.leads import delete_demo_leads
	from crm.demo.notes import delete_demo_notes
	from crm.demo.tasks import delete_demo_tasks
	from crm.demo.users import DEMO_USER_EMAILS, delete_demo_users

	lead_names = json.loads(frappe.db.get_default(DEMO_LEADS_KEY) or "[]")
	note_names = json.loads(frappe.db.get_default(DEMO_NOTES_KEY) or "[]")
	task_names = json.loads(frappe.db.get_default(DEMO_TASKS_KEY) or "[]")
	delete_demo_notes(note_names)
	delete_demo_tasks(task_names)
	delete_demo_leads(lead_names)
	delete_demo_users(DEMO_USER_EMAILS)
	frappe.db.set_default(DEMO_LEADS_KEY, None)
	frappe.db.set_default(DEMO_NOTES_KEY, None)
	frappe.db.set_default(DEMO_TASKS_KEY, None)
	frappe.db.set_default(DEMO_STATE_KEY, None)


@frappe.whitelist()
def get_demo_state():
	return {"demo_data_created": bool(frappe.db.get_default(DEMO_STATE_KEY))}
