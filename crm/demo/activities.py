from datetime import datetime, timedelta

import frappe

from crm.demo.utils import (
	build_full_names,
	insert_comment,
	insert_communication,
	insert_version,
	resolve_owners,
)


def create_demo_activities(lead_names, demo_users):
	"""Create comments, email communications, and field-change versions for demo leads."""
	session_user, owner_1, owner_2, _ = resolve_owners(demo_users)
	_full_names = build_full_names(session_user)

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
			"days_ago": 56,  # lead[0] deal created at 50 days ago — keep before that
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
			"days_ago": 41,  # lead[3] deal created at 37 days ago — keep before that
		},
	]

	return [
		insert_comment(
			"CRM Lead",
			data["lead"],
			data["owner"],
			data["content"],
			full_names,
			now - timedelta(days=data["days_ago"]),
		)
		for data in comments_data
	]


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
			"days_ago": 54,  # lead[0] deal at 50 days ago — keep before that
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
			"days_ago": 39,  # lead[3] deal at 37 days ago — keep before that
		},
	]

	return [
		insert_communication(
			"CRM Lead", data["lead"], data, full_names, now - timedelta(days=data["days_ago"])
		)
		for data in comms_data
	]


def _create_versions(lead_names, session_user, owner_1, owner_2, now):
	versions_data = [
		{
			"lead": lead_names[0],
			"owner": session_user,
			"changed": [["no_of_employees", "201-500", "501-1000"]],
			"days_ago": 52,  # lead[0] deal at 50 days ago — keep before that
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
			"days_ago": 38,  # lead[3] deal at 37 days ago — keep before that
		},
	]

	for data in versions_data:
		insert_version(
			"CRM Lead", data["lead"], data["owner"], data["changed"], now - timedelta(days=data["days_ago"])
		)


def delete_demo_activities(activity_data):
	"""Delete communications (comments and versions are cascade-deleted with their lead)."""
	communication_names = activity_data.get("communications", [])
	for name in communication_names:
		if frappe.db.exists("Communication", name):
			frappe.delete_doc("Communication", name, ignore_permissions=True, force=True)
