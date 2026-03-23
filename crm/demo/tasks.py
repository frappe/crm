import frappe
from frappe.query_builder import DocType


def create_demo_tasks(lead_names, demo_users):
	from datetime import date, timedelta

	today = date.today()
	owner_1 = demo_users[0] if len(demo_users) > 0 else frappe.session.user
	owner_2 = demo_users[1] if len(demo_users) > 1 else frappe.session.user

	tasks_data = [
		{
			"title": "Send proposal document",
			"priority": "High",
			"status": "Todo",
			"assigned_to": frappe.session.user,
			"due_date": today + timedelta(days=2),
			"reference_doctype": "CRM Lead",
			"reference_docname": lead_names[0],
			"description": "Prepare and send a tailored proposal covering pricing, integrations, and onboarding timeline.",
		},
		{
			"title": "Schedule technical demo",
			"priority": "Medium",
			"status": "In Progress",
			"assigned_to": owner_1,
			"due_date": today + timedelta(days=5),
			"reference_doctype": "CRM Lead",
			"reference_docname": lead_names[0],
			"description": "Coordinate with the CTO to set up a 1-hour technical deep-dive session.",
		},
		{
			"title": "Follow up on trial access",
			"priority": "High",
			"status": "Todo",
			"assigned_to": owner_1,
			"due_date": today + timedelta(days=1),
			"reference_doctype": "CRM Lead",
			"reference_docname": lead_names[1],
			"description": "Check in on trial progress and address any blockers before the next call.",
		},
		{
			"title": "Send competitor comparison doc",
			"priority": "Medium",
			"status": "Done",
			"assigned_to": owner_2,
			"due_date": today - timedelta(days=2),
			"reference_doctype": "CRM Lead",
			"reference_docname": lead_names[1],
			"description": "Share the feature comparison sheet highlighting our advantages over the competitor they're trialing.",
		},
		{
			"title": "Set up trial environment",
			"priority": "High",
			"status": "In Progress",
			"assigned_to": owner_2,
			"due_date": today + timedelta(days=3),
			"reference_doctype": "CRM Lead",
			"reference_docname": lead_names[2],
			"description": "Provision a trial instance with sample data pre-loaded for their team to evaluate.",
		},
		{
			"title": "Confirm annual plan details",
			"priority": "Low",
			"status": "Backlog",
			"assigned_to": frappe.session.user,
			"due_date": today + timedelta(days=10),
			"reference_doctype": "CRM Lead",
			"reference_docname": lead_names[3],
			"description": "Finalize seat count and send updated quote for annual subscription.",
		},
	]

	created = []
	for data in tasks_data:
		task = frappe.get_doc({"doctype": "CRM Task", **data}).insert(ignore_permissions=True)
		created.append(task.name)

	return created


def delete_demo_tasks(task_names):
	for name in task_names:
		if frappe.db.exists("CRM Task", name):
			frappe.delete_doc("CRM Task", name, ignore_permissions=True, force=True)
