from datetime import datetime, timedelta

import frappe
from frappe.query_builder import DocType

from crm.demo.utils import (
	backdate,
	build_full_names,
	fix_auto_records,
	insert_comment,
	insert_communication,
	insert_version,
	resolve_owners,
)


def create_demo_deals(lead_names, demo_users):
	"""Convert seven leads into deals and add deal-specific activity."""
	from crm.fcrm.doctype.crm_lead.crm_lead import convert_to_deal

	session_user, owner_1, owner_2, _ = resolve_owners(demo_users)
	_full_names = build_full_names(session_user)

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
			"lost_reason": "Competition",
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
	# Converted lead indices — must match deal_names_list order
	_converted_lead_indices = [0, 3, 7, 8, 9, 10, 11]
	# Days ago each deal was created (always after its lead)
	_deal_days = [50, 37, 18, 11, 24, 9, 5]
	_deal_owners = [session_user, owner_1, owner_2, session_user, owner_1, owner_2, session_user]
	# Organization logos keyed by org name (index order: alice, david, henry, iris, jack, karen, leo)
	_org_logos = {
		"Acme Corp": "/assets/crm/images/demo/acme-corp.png",
		"TechStart Inc": "/assets/crm/images/demo/techstart-inc.png",
		"PivotTech Solutions": "/assets/crm/images/demo/pivottech-solutions.png",
		"ScaleUp Labs": "/assets/crm/images/demo/scaleup-labs.png",
		"Meridian Systems": "/assets/crm/images/demo/meridian-systems.png",
		"Vertex Analytics": "/assets/crm/images/demo/vertex-analytics.png",
		"Forge Digital": "/assets/crm/images/demo/forge-digital.png",
	}
	now = datetime.now()

	for d_name, days, d_owner, li in zip(
		deal_names_list, _deal_days, _deal_owners, _converted_lead_indices, strict=False
	):
		ts = now - timedelta(days=days)
		backdate("CRM Deal", d_name, d_owner, ts)
		org = frappe.db.get_value("CRM Deal", d_name, "organization")
		if org:
			logo = _org_logos.get(org)
			if logo:
				frappe.db.set_value("CRM Organization", org, "organization_logo", logo, update_modified=False)
			backdate("CRM Organization", org, d_owner, ts)
		contacts = frappe.get_all(
			"CRM Contacts", filters={"parent": d_name, "parenttype": "CRM Deal"}, pluck="contact"
		)
		for contact in contacts:
			if contact:
				backdate("Contact", contact, d_owner, ts)
		backdate("CRM Lead", lead_names[li], d_owner, ts, set_creation=False)
		fix_auto_records("CRM Deal", d_name, d_owner, ts)
		fix_auto_records("CRM Lead", lead_names[li], d_owner, ts)

	comment_names = _create_deal_comments(deal_names_list, session_user, owner_1, owner_2, _full_names, now)
	communication_names = _create_deal_communications(
		deal_names_list, session_user, owner_1, _full_names, now
	)
	_create_deal_versions(deal_names_list, session_user, owner_1, owner_2, now)

	# Re-backdate modified to last-activity date so active deals sort to the top of the list.
	# Index order: alice, david, henry, iris, jack, karen, leo
	_deal_last_touched_days = [2, 4, 7, 10, 6, 8, 12]
	for d_name, days, d_owner in zip(deal_names_list, _deal_last_touched_days, _deal_owners, strict=False):
		backdate("CRM Deal", d_name, d_owner, now - timedelta(days=days), set_creation=False)

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

	return [
		insert_comment(
			"CRM Deal",
			data["deal"],
			data["owner"],
			data["content"],
			full_names,
			now - timedelta(days=data["days_ago"]),
		)
		for data in comments_data
	]


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

	return [
		insert_communication(
			"CRM Deal", data["deal"], data, full_names, now - timedelta(days=data["days_ago"])
		)
		for data in comms_data
	]


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
		insert_version(
			"CRM Deal", data["deal"], data["owner"], data["changed"], now - timedelta(days=data["days_ago"])
		)


def delete_demo_deals(deal_data, lead_names):
	"""
	Delete deals, their linked contacts, organizations, and deal-specific communications.
	Comments and Versions are cascade-deleted when the deal is deleted.
	"""
	communication_names = deal_data.get("communications", [])
	deal_names = set(deal_data.get("deals", []))

	# Find all deals converted from the provided demo leads
	if lead_names:
		demo_lead_deals = frappe.get_all("CRM Deal", filters={"lead": ["in", lead_names]}, pluck="name")
		deal_names.update(demo_lead_deals)

	for name in communication_names:
		if frappe.db.exists("Communication", name):
			frappe.delete_doc("Communication", name, ignore_permissions=True, force=True)

	for name in deal_names:
		if not frappe.db.exists("CRM Deal", name):
			continue
		# Collect linked contacts and organization before deleting deal
		contact_names = frappe.get_all(
			"CRM Contacts", filters={"parent": name, "parenttype": "CRM Deal"}, pluck="contact"
		)
		org = frappe.db.get_value("CRM Deal", name, "organization")
		frappe.delete_doc("CRM Deal", name, ignore_permissions=True, force=True)
		for contact in contact_names:
			if contact and frappe.db.exists("Contact", contact):
				for child_doctype in ("Contact Email", "Contact Phone", "Dynamic Link"):
					Child = DocType(child_doctype)
					frappe.qb.from_(Child).delete().where(Child.parent == contact).run()
				Contact = DocType("Contact")
				frappe.qb.from_(Contact).delete().where(Contact.name == contact).run()
		if org and frappe.db.exists("CRM Organization", org):
			frappe.delete_doc("CRM Organization", org, ignore_permissions=True, force=True)
