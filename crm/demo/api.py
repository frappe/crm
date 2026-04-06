import json

import frappe
from frappe.utils.telemetry import capture

DEMO_STATE_KEY = "crm_demo_data_created"
DEMO_LEADS_KEY = "crm_demo_leads"
DEMO_NOTES_KEY = "crm_demo_notes"
DEMO_TASKS_KEY = "crm_demo_tasks"
DEMO_CALL_LOGS_KEY = "crm_demo_call_logs"
DEMO_ACTIVITIES_KEY = "crm_demo_activities"
DEMO_DEALS_KEY = "crm_demo_deals"


def create_demo_data(_args: dict | None = None):
	if frappe.db.get_default(DEMO_STATE_KEY):
		return

	from crm.demo.activities import create_demo_activities
	from crm.demo.call_logs import create_demo_call_logs
	from crm.demo.deals import create_demo_deals
	from crm.demo.leads import create_demo_leads
	from crm.demo.notes import create_demo_notes
	from crm.demo.tasks import create_demo_tasks
	from crm.demo.users import create_demo_users

	demo_users = create_demo_users()
	lead_names = create_demo_leads(demo_users)
	note_names = create_demo_notes(lead_names, demo_users)
	task_names = create_demo_tasks(lead_names, demo_users)
	call_log_names = create_demo_call_logs(lead_names, demo_users)
	activity_data = create_demo_activities(lead_names, demo_users)

	from crm.demo.leads import rebackdate_demo_leads

	rebackdate_demo_leads(lead_names, demo_users)

	deal_data = create_demo_deals(lead_names, demo_users)
	frappe.db.set_default(DEMO_LEADS_KEY, json.dumps(lead_names))
	frappe.db.set_default(DEMO_NOTES_KEY, json.dumps(note_names))
	frappe.db.set_default(DEMO_TASKS_KEY, json.dumps(task_names))
	frappe.db.set_default(DEMO_CALL_LOGS_KEY, json.dumps(call_log_names))
	frappe.db.set_default(DEMO_ACTIVITIES_KEY, json.dumps(activity_data))
	frappe.db.set_default(DEMO_DEALS_KEY, json.dumps(deal_data))
	frappe.db.set_default(DEMO_STATE_KEY, "1")

	capture("demo_data_created", "crm")


@frappe.whitelist()
def clear_demo_data():
	frappe.only_for(["Sales Manager", "System Manager"], True)

	if not frappe.db.get_default(DEMO_STATE_KEY):
		return

	from crm.demo.activities import delete_demo_activities
	from crm.demo.call_logs import delete_demo_call_logs
	from crm.demo.deals import delete_demo_deals
	from crm.demo.leads import delete_demo_leads
	from crm.demo.notes import delete_demo_notes
	from crm.demo.tasks import delete_demo_tasks
	from crm.demo.users import DEMO_USER_EMAILS, delete_demo_users

	lead_names = json.loads(frappe.db.get_default(DEMO_LEADS_KEY) or "[]")
	note_names = json.loads(frappe.db.get_default(DEMO_NOTES_KEY) or "[]")
	task_names = json.loads(frappe.db.get_default(DEMO_TASKS_KEY) or "[]")
	call_log_names = json.loads(frappe.db.get_default(DEMO_CALL_LOGS_KEY) or "[]")
	activity_data = json.loads(frappe.db.get_default(DEMO_ACTIVITIES_KEY) or "{}")
	deal_data = json.loads(frappe.db.get_default(DEMO_DEALS_KEY) or "{}")
	delete_demo_deals(deal_data, lead_names)
	delete_demo_activities(activity_data)
	delete_demo_notes(note_names)
	delete_demo_tasks(task_names)
	delete_demo_call_logs(call_log_names)
	delete_demo_leads(lead_names)
	delete_demo_users(DEMO_USER_EMAILS)
	frappe.db.set_default(DEMO_LEADS_KEY, None)
	frappe.db.set_default(DEMO_NOTES_KEY, None)
	frappe.db.set_default(DEMO_TASKS_KEY, None)
	frappe.db.set_default(DEMO_CALL_LOGS_KEY, None)
	frappe.db.set_default(DEMO_ACTIVITIES_KEY, None)
	frappe.db.set_default(DEMO_DEALS_KEY, None)
	frappe.db.set_default(DEMO_STATE_KEY, None)

	capture("demo_data_cleared", "crm")


@frappe.whitelist()
def get_demo_state():
	return {"demo_data_created": bool(frappe.db.get_default(DEMO_STATE_KEY))}
