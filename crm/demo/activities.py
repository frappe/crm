import json
from datetime import datetime, timedelta

import frappe


def create_demo_activities(lead_names, demo_users):
	"""Create comments, email communications, and field-change versions for demo leads."""
	from crm.demo.users import DEMO_USERS

	session_user = frappe.session.user
	owner_1 = demo_users[0] if len(demo_users) > 0 else session_user
	owner_2 = demo_users[1] if len(demo_users) > 1 else session_user

	# Build full-name lookup
	_full_names = {u["email"]: f"{u['first_name']} {u['last_name']}" for u in DEMO_USERS}
	_full_names[session_user] = frappe.utils.get_fullname(session_user)

	now = datetime.now()

	comment_names = _create_comments(lead_names, session_user, owner_1, owner_2, _full_names, now)
	communication_names = _create_communications(lead_names, session_user, owner_1, _full_names, now)
	_create_versions(lead_names, session_user, owner_1, owner_2, now)

	return {"comments": comment_names, "communications": communication_names}


def _create_comments(lead_names, session_user, owner_1, owner_2, full_names, now):
	comments_data = [
		{
			"lead": lead_names[0],
			"owner": session_user,
			"content": (
				"<p>Initial discovery call was very productive. Alice's team of ~300 engineers is actively "
				"evaluating CRM solutions. She mentioned budget has already been approved — just need "
				"to get sign-off from the VP of Sales.</p>"
			),
			"days_ago": 6,
		},
		{
			"lead": lead_names[1],
			"owner": owner_1,
			"content": (
				"<p>Bob mentioned they had a poor experience with their last CRM. He emphasized that "
				"onboarding support and data migration are top priorities. Need to loop in the "
				"customer success team before the next call.</p>"
			),
			"days_ago": 9,
		},
		{
			"lead": lead_names[2],
			"owner": owner_2,
			"content": (
				"<p>Carol is temporarily unavailable — on leave until end of month. Her colleague "
				"Mark is the interim contact. Revisit in 3 weeks with updated pricing deck.</p>"
			),
			"days_ago": 11,
		},
		{
			"lead": lead_names[3],
			"owner": owner_1,
			"content": (
				"<p>Technical demo completed successfully. David's engineering team was impressed with "
				"the API and custom field options. He's requesting pricing for 15 seats — send "
				"the proposal by Friday.</p>"
			),
			"days_ago": 14,
		},
	]

	created = []
	for data in comments_data:
		ts = now - timedelta(days=data["days_ago"])
		comment = frappe.get_doc(
			{
				"doctype": "Comment",
				"comment_type": "Comment",
				"reference_doctype": "CRM Lead",
				"reference_name": data["lead"],
				"content": data["content"],
				"comment_email": data["owner"],
				"comment_by": full_names.get(data["owner"], data["owner"]),
			}
		)
		comment.owner = data["owner"]
		comment.modified_by = data["owner"]
		comment.creation = ts
		comment.modified = ts
		comment.insert(ignore_permissions=True)
		created.append(comment.name)

	return created


def _create_communications(lead_names, session_user, owner_1, full_names, now):
	# Lead emails used for recipient/sender fields
	lead_emails = {
		lead_names[0]: "alice.johnson@example.com",
		lead_names[1]: "bob.martinez@example.com",
		lead_names[3]: "david.lee@example.com",
	}

	comms_data = [
		{
			"lead": lead_names[0],
			"owner": session_user,
			"sent_or_received": "Sent",
			"subject": "Following up on our discovery call — Acme Corp",
			"content": (
				"<p>Hi Alice,</p>"
				"<p>It was great speaking with you earlier today. As discussed, I'm sharing our "
				"product overview and a link to schedule a full demo with your team.</p>"
				"<p>Please let me know if you have any questions before we meet.</p>"
				"<p>Best regards</p>"
			),
			"sender": session_user,
			"recipients": lead_emails[lead_names[0]],
			"days_ago": 5,
		},
		{
			"lead": lead_names[1],
			"owner": owner_1,
			"sent_or_received": "Received",
			"subject": "Re: CRM Demo Request — Globex Industries",
			"content": (
				"<p>Hi,</p>"
				"<p>Thanks for reaching out. We'd definitely like to see a live demo, specifically "
				"around pipeline management and email integration. Can we schedule something for "
				"next Tuesday at 2 PM?</p>"
				"<p>Best,<br>Bob Martinez<br>CEO, Globex Industries</p>"
			),
			"sender": lead_emails[lead_names[1]],
			"recipients": owner_1,
			"days_ago": 8,
		},
		{
			"lead": lead_names[3],
			"owner": owner_1,
			"sent_or_received": "Sent",
			"subject": "CRM Pricing Proposal — TechStart Inc (15 seats)",
			"content": (
				"<p>Hi David,</p>"
				"<p>Great connecting with your team today — really glad the API walkthrough was "
				"useful. Attached is our pricing proposal for 15 seats including onboarding and "
				"priority support.</p>"
				"<p>Happy to jump on a call if you have questions.</p>"
				"<p>Cheers</p>"
			),
			"sender": owner_1,
			"recipients": lead_emails[lead_names[3]],
			"days_ago": 13,
		},
	]

	created = []
	for data in comms_data:
		ts = now - timedelta(days=data["days_ago"])
		sender_full = full_names.get(data["sender"], data["sender"])
		comm = frappe.get_doc(
			{
				"doctype": "Communication",
				"communication_type": "Communication",
				"communication_medium": "Email",
				"status": "Linked",
				"sent_or_received": data["sent_or_received"],
				"reference_doctype": "CRM Lead",
				"reference_name": data["lead"],
				"subject": data["subject"],
				"content": data["content"],
				"sender": data["sender"],
				"sender_full_name": sender_full,
				"recipients": data["recipients"],
				"communication_date": ts,
			}
		)
		comm.owner = data["owner"]
		comm.modified_by = data["owner"]
		comm.creation = ts
		comm.modified = ts
		comm.insert(ignore_permissions=True)
		created.append(comm.name)

	return created


def _create_versions(lead_names, session_user, owner_1, owner_2, now):
	versions_data = [
		{
			"lead": lead_names[0],
			"owner": session_user,
			"changed": [["no_of_employees", "201-500", "501-1000"]],
			"days_ago": 7,
		},
		{
			"lead": lead_names[1],
			"owner": owner_1,
			"changed": [["annual_revenue", None, "10000000"]],
			"days_ago": 10,
		},
		{
			"lead": lead_names[2],
			"owner": owner_2,
			"changed": [["source", "Email", "Referral"]],
			"days_ago": 12,
		},
		{
			"lead": lead_names[3],
			"owner": owner_1,
			"changed": [["status", "Contacted", "Qualified"]],
			"days_ago": 15,
		},
	]

	for data in versions_data:
		ts = now - timedelta(days=data["days_ago"])
		version = frappe.get_doc(
			{
				"doctype": "Version",
				"ref_doctype": "CRM Lead",
				"docname": data["lead"],
				"data": json.dumps({"changed": data["changed"]}),
			}
		)
		version.owner = data["owner"]
		version.modified_by = data["owner"]
		version.creation = ts
		version.modified = ts
		version.insert(ignore_permissions=True)


def delete_demo_activities(activity_data):
	"""Delete communications (comments and versions are cascade-deleted with their lead)."""
	communication_names = activity_data.get("communications", [])
	for name in communication_names:
		if frappe.db.exists("Communication", name):
			frappe.delete_doc("Communication", name, ignore_permissions=True, force=True)
