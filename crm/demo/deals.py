import json
from datetime import datetime, timedelta

import frappe


def create_demo_deals(lead_names, demo_users):
	"""Convert five leads into deals and add deal-specific activity."""
	from crm.demo.users import DEMO_USERS
	from crm.fcrm.doctype.crm_lead.crm_lead import convert_to_deal

	session_user = frappe.session.user
	owner_1 = demo_users[0] if len(demo_users) > 0 else session_user
	owner_2 = demo_users[1] if len(demo_users) > 1 else session_user

	_full_names = {u["email"]: f"{u['first_name']} {u['last_name']}" for u in DEMO_USERS}
	_full_names[session_user] = frappe.utils.get_fullname(session_user)

	# leads[0] Alice, [3] David, [7] Henry, [8] Iris, [9] Jack → 5 active/won deals
	# leads[10] Karen, [11] Leo → 2 lost deals
	d_alice = convert_to_deal(
		lead=lead_names[0],
		deal={"status": "Demo/Making", "deal_value": 120000, "probability": 50, "deal_owner": session_user},
	)
	d_david = convert_to_deal(
		lead=lead_names[3],
		deal={"status": "Proposal/Quotation", "deal_value": 45000, "probability": 70, "deal_owner": owner_1},
	)
	d_henry = convert_to_deal(
		lead=lead_names[7],
		deal={"status": "Negotiation", "deal_value": 85000, "probability": 60, "deal_owner": owner_2},
	)
	d_iris = convert_to_deal(
		lead=lead_names[8],
		deal={"status": "Qualification", "deal_value": 60000, "probability": 35, "deal_owner": session_user},
	)
	d_jack = convert_to_deal(
		lead=lead_names[9],
		deal={"status": "Won", "deal_value": 175000, "probability": 100, "deal_owner": owner_1},
	)
	d_karen = convert_to_deal(
		lead=lead_names[10],
		deal={
			"status": "Lost",
			"deal_value": 95000,
			"probability": 0,
			"deal_owner": owner_2,
			"lost_reason": "Competitor",
			"lost_notes": "Prospect chose a competitor offering deeper BI integrations out of the box. Price was not the issue — feature parity was.",
		},
	)
	d_leo = convert_to_deal(
		lead=lead_names[11],
		deal={
			"status": "Lost",
			"deal_value": 55000,
			"probability": 0,
			"deal_owner": session_user,
			"lost_reason": "Budget constraints",
			"lost_notes": "Q2 budget was cut. Leo said they would revisit in Q4 once headcount hiring is complete. Added to nurture sequence.",
		},
	)

	deal_names_list = [d_alice, d_david, d_henry, d_iris, d_jack, d_karen, d_leo]
	now = datetime.now()

	comment_names = _create_deal_comments(deal_names_list, session_user, owner_1, owner_2, _full_names, now)
	communication_names = _create_deal_communications(
		deal_names_list, session_user, owner_1, _full_names, now
	)
	_create_deal_versions(deal_names_list, session_user, owner_1, owner_2, now)

	return {
		"deals": deal_names_list,
		"comments": comment_names,
		"communications": communication_names,
	}


def _create_deal_comments(deal_names, session_user, owner_1, owner_2, full_names, now):
	comments_data = [
		{
			"deal": deal_names[0],  # Alice / Acme Corp
			"owner": session_user,
			"content": (
				"<p>Live demo went well — Alice's product team joined and had great questions "
				"about workflow automation and bulk import. They want a custom sandbox environment "
				"to evaluate with their own data before signing. Following up to arrange access.</p>"
			),
			"days_ago": 3,
		},
		{
			"deal": deal_names[1],  # David / TechStart Inc
			"owner": owner_1,
			"content": (
				"<p>David reviewed the proposal with his co-founder. They're happy with the pricing "
				"but want a 3-month pilot before committing to annual. Checking with management on "
				"whether we can offer a pilot discount.</p>"
			),
			"days_ago": 5,
		},
		{
			"deal": deal_names[2],  # Henry / PivotTech Solutions
			"owner": owner_2,
			"content": (
				"<p>Negotiation call with Henry went long but productive. He’s pushing for a 15% "
				"discount on the annual plan citing budget constraints. Legal team is now reviewing "
				"the contract — decision expected by end of week.</p>"
			),
			"days_ago": 7,
		},
		{
			"deal": deal_names[3],  # Iris / ScaleUp Labs
			"owner": session_user,
			"content": (
				"<p>Qualification call completed with Iris and her co-founder. Small but fast-moving "
				"team of 8 engineers. Main concerns are API depth and self-serve onboarding. "
				"Sending over the developer docs and scheduling a technical deep-dive.</p>"
			),
			"days_ago": 10,
		},
		{
			"deal": deal_names[4],  # Jack / Meridian Systems
			"owner": owner_1,
			"content": (
				"<p>Deal closed — Jack signed the contract this morning. Final value $175k annual. "
				"Onboarding is scheduled for next Monday. Handoff notes sent to the customer "
				"success team. Great result for the quarter!</p>"
			),
			"days_ago": 2,
		},
		{
			"deal": deal_names[5],  # Karen / Vertex Analytics
			"owner": owner_2,
			"content": (
				"<p>Karen's team went with a competitor — they had deeper BI integrations that we "
				"currently don't support. Not a pricing issue. Flagged to product team for roadmap "
				"consideration. Karen asked us to follow up in 6 months.</p>"
			),
			"days_ago": 8,
		},
		{
			"deal": deal_names[6],  # Leo / Forge Digital
			"owner": session_user,
			"content": (
				"<p>Budget was cut for the rest of the year — Leo was very apologetic and said the "
				"product was exactly what they needed. Re-added to nurture sequence for Q4. "
				"Good candidate for a comeback deal.</p>"
			),
			"days_ago": 12,
		},
	]

	created = []
	for data in comments_data:
		ts = now - timedelta(days=data["days_ago"])
		comment = frappe.get_doc(
			{
				"doctype": "Comment",
				"comment_type": "Comment",
				"reference_doctype": "CRM Deal",
				"reference_name": data["deal"],
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


def _create_deal_communications(deal_names, session_user, owner_1, full_names, now):
	# Use a placeholder email for recipients where we don't have a real one handy
	comms_data = [
		{
			"deal": deal_names[0],
			"owner": session_user,
			"sent_or_received": "Sent",
			"subject": "Sandbox access details — Acme Corp CRM Evaluation",
			"content": (
				"<p>Hi Alice,</p>"
				"<p>Thanks for joining yesterday's demo — really great session. I've created a "
				"dedicated sandbox environment pre-loaded with sample data. Login details and "
				"setup instructions are attached.</p>"
				"<p>Our onboarding specialist Sarah will also be available for a walkthrough "
				"session this week — just let us know a convenient time.</p>"
				"<p>Best regards</p>"
			),
			"sender": session_user,
			"recipients": "alice.johnson@example.com",
			"days_ago": 2,
		},
		{
			"deal": deal_names[1],
			"owner": owner_1,
			"sent_or_received": "Received",
			"subject": "Re: CRM Proposal — Pilot terms query",
			"content": (
				"<p>Hi,</p>"
				"<p>We've reviewed the proposal and the pricing looks good. Before we proceed, "
				"could you clarify what's included in the onboarding package? Specifically, we "
				"need help migrating ~4,000 contacts from our existing system.</p>"
				"<p>Also, is there flexibility on the contract start date?</p>"
				"<p>Thanks,<br>David Lee<br>CTO, TechStart Inc</p>"
			),
			"sender": "david.lee@example.com",
			"recipients": owner_1,
			"days_ago": 4,
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
				"reference_doctype": "CRM Deal",
				"reference_name": data["deal"],
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


def _create_deal_versions(deal_names, session_user, owner_1, owner_2, now):
	versions_data = [
		{
			"deal": deal_names[0],  # Alice
			"owner": session_user,
			"changed": [["probability", "30", "50"]],
			"days_ago": 4,
		},
		{
			"deal": deal_names[1],  # David
			"owner": owner_1,
			"changed": [["deal_value", "40000", "45000"]],
			"days_ago": 6,
		},
		{
			"deal": deal_names[2],  # Henry
			"owner": owner_2,
			"changed": [["probability", "50", "60"]],
			"days_ago": 8,
		},
		{
			"deal": deal_names[3],  # Iris
			"owner": session_user,
			"changed": [["probability", "25", "35"]],
			"days_ago": 11,
		},
		{
			"deal": deal_names[4],  # Jack
			"owner": owner_1,
			"changed": [["status", "Ready to Close", "Won"]],
			"days_ago": 3,
		},
		{
			"deal": deal_names[5],  # Karen
			"owner": owner_2,
			"changed": [["status", "Proposal/Quotation", "Lost"]],
			"days_ago": 9,
		},
		{
			"deal": deal_names[6],  # Leo
			"owner": session_user,
			"changed": [["status", "Demo/Making", "Lost"]],
			"days_ago": 13,
		},
	]

	for data in versions_data:
		ts = now - timedelta(days=data["days_ago"])
		version = frappe.get_doc(
			{
				"doctype": "Version",
				"ref_doctype": "CRM Deal",
				"docname": data["deal"],
				"data": json.dumps({"changed": data["changed"]}),
			}
		)
		version.owner = data["owner"]
		version.modified_by = data["owner"]
		version.creation = ts
		version.modified = ts
		version.insert(ignore_permissions=True)


def delete_demo_deals(deal_data):
	"""
	Delete deals, their linked organizations, and deal-specific communications.
	Comments and Versions are cascade-deleted when the deal is deleted.
	Contacts are shared with leads — deleted by delete_demo_users.
	"""
	communication_names = deal_data.get("communications", [])
	deal_names = deal_data.get("deals", [])

	for name in communication_names:
		if frappe.db.exists("Communication", name):
			frappe.delete_doc("Communication", name, ignore_permissions=True, force=True)

	for name in deal_names:
		if not frappe.db.exists("CRM Deal", name):
			continue
		# Collect linked organization before deleting deal
		org = frappe.db.get_value("CRM Deal", name, "organization")
		frappe.delete_doc("CRM Deal", name, ignore_permissions=True, force=True)
		if org and frappe.db.exists("CRM Organization", org):
			frappe.delete_doc("CRM Organization", org, ignore_permissions=True, force=True)
