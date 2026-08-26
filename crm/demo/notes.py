from datetime import datetime, timedelta

import frappe

from crm.demo.utils import backdate, resolve_owners


def create_demo_notes(lead_names, demo_users):
	session_user, owner_1, owner_2, _ = resolve_owners(demo_users)
	now = datetime.now()

	# Two notes per lead — a call summary and a follow-up observation
	notes_data = [
		{
			"title": "Initial Discovery Call",
			"content": "<p>Had a productive intro call. They're evaluating solutions for Q3. Key stakeholders include the CTO and VP of Sales. Budget is pre-approved. Follow up with a tailored proposal.</p>",
			"reference_doctype": "CRM Lead",
			"reference_docname": lead_names[0],
			"owner": session_user,
			"days_ago": 56,
		},
		{
			"title": "Pain Points Identified",
			"content": "<p>Current system lacks reporting and integrations. Team size is growing fast — 40% headcount increase this year. Decision timeline is 6–8 weeks.</p>",
			"reference_doctype": "CRM Lead",
			"reference_docname": lead_names[0],
			"owner": session_user,
			"days_ago": 51,
		},
		{
			"title": "Demo Feedback",
			"content": "<p>Very positive response to the pipeline view. Asked about custom fields and API access. Needs sign-off from CFO before moving forward.</p>",
			"reference_doctype": "CRM Lead",
			"reference_docname": lead_names[1],
			"owner": owner_1,
			"days_ago": 46,
		},
		{
			"title": "Competitor Mentioned",
			"content": "<p>Currently trialing a competitor. Our differentiators: better UX, open source, and lower TCO. Send a comparison doc before next call.</p>",
			"reference_doctype": "CRM Lead",
			"reference_docname": lead_names[1],
			"owner": owner_1,
			"days_ago": 39,
		},
		{
			"title": "Requirements Gathered",
			"content": "<p>Needs CRM + email integration + team collaboration. Currently using spreadsheets. Strong motivation to move to a structured system this quarter.</p>",
			"reference_doctype": "CRM Lead",
			"reference_docname": lead_names[2],
			"owner": owner_2,
			"days_ago": 44,
		},
		{
			"title": "Pricing Discussion",
			"content": "<p>Walked through pricing tiers. They prefer an annual plan. Requested a 2-week trial extension. Champion is very engaged — internal buy-in looks strong.</p>",
			"reference_doctype": "CRM Lead",
			"reference_docname": lead_names[3],
			"owner": owner_1,
			"days_ago": 40,
		},
	]

	created = []
	for data in notes_data:
		ts = now - timedelta(days=data["days_ago"])
		owner = data["owner"]
		note = frappe.get_doc(
			{
				"doctype": "FCRM Note",
				"title": data["title"],
				"content": data["content"],
				"reference_doctype": data["reference_doctype"],
				"reference_docname": data["reference_docname"],
			}
		).insert(ignore_permissions=True)
		backdate("FCRM Note", note.name, owner, ts)
		created.append(note.name)

	return created


def delete_demo_notes(note_names):
	for name in note_names:
		if frappe.db.exists("FCRM Note", name):
			frappe.delete_doc("FCRM Note", name, ignore_permissions=True, force=True)
