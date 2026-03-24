import frappe

from crm.demo.utils import backdate, resolve_owners


def create_demo_tasks(lead_names, demo_users):
	from datetime import date, datetime, timedelta

	today = date.today()
	now = datetime.now()
	session_user, owner_1, owner_2, _ = resolve_owners(demo_users)

	tasks_data = [
		{
			"title": "Send proposal document",
			"priority": "High",
			"status": "Todo",
			"assigned_to": session_user,
			"due_date": today + timedelta(days=2),
			"reference_doctype": "CRM Lead",
			"reference_docname": lead_names[0],
			"description": "Prepare and send a tailored proposal covering pricing, integrations, and onboarding timeline.",
			"days_ago": 1,
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
			"days_ago": 3,
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
			"days_ago": 2,
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
			"days_ago": 6,
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
			"days_ago": 3,
		},
		{
			"title": "Confirm annual plan details",
			"priority": "Low",
			"status": "Backlog",
			"assigned_to": session_user,
			"due_date": today + timedelta(days=10),
			"reference_doctype": "CRM Lead",
			"reference_docname": lead_names[3],
			"description": "Finalize seat count and send updated quote for annual subscription.",
			"days_ago": 1,
		},
	]

	created = []
	for data in tasks_data:
		owner = data["assigned_to"]
		ts = now - timedelta(days=data.pop("days_ago"))
		task = frappe.get_doc({"doctype": "CRM Task", **data}).insert(ignore_permissions=True)
		backdate("CRM Task", task.name, owner, ts)
		created.append(task.name)

	return created


def delete_demo_tasks(task_names):
	for name in task_names:
		if frappe.db.exists("CRM Task", name):
			frappe.delete_doc("CRM Task", name, ignore_permissions=True, force=True)
