import frappe

from crm.demo.users import DEMO_USERS
from crm.demo.utils import resolve_owners


def create_demo_call_logs(lead_names, demo_users):
	from datetime import datetime, timedelta

	now = datetime.now()
	session_user, owner_1, owner_2, _ = resolve_owners(demo_users)

	# Build rep phone number map from DEMO_USERS mobile numbers
	_user_mobile = {u["email"]: u["mobile_no"] for u in DEMO_USERS}
	rep_numbers = {
		session_user: _user_mobile.get(session_user, "+1 555 100 0001"),
		owner_1: _user_mobile.get(owner_1, "+1 555 100 0002"),
		owner_2: _user_mobile.get(owner_2, "+1 555 100 0003"),
	}

	call_logs_data = [
		{
			"type": "Outgoing",
			"status": "Completed",
			"telephony_medium": "Manual",
			"duration": 720,
			"from": rep_numbers[session_user],
			"to": "+1 555 000 1234",
			"caller": session_user,
			"start_time": now - timedelta(days=5, hours=2),
			"end_time": now - timedelta(days=5, hours=2) + timedelta(seconds=720),
			"reference_doctype": "CRM Lead",
			"reference_docname": lead_names[0],
		},
		{
			"type": "Incoming",
			"status": "Completed",
			"telephony_medium": "Manual",
			"duration": 300,
			"from": "+1 555 000 1234",
			"to": rep_numbers[session_user],
			"receiver": session_user,
			"start_time": now - timedelta(days=2, hours=1),
			"end_time": now - timedelta(days=2, hours=1) + timedelta(seconds=300),
			"reference_doctype": "CRM Lead",
			"reference_docname": lead_names[0],
		},
		{
			"type": "Outgoing",
			"status": "Completed",
			"telephony_medium": "Manual",
			"duration": 540,
			"from": rep_numbers[owner_1],
			"to": "+1 555 000 5678",
			"caller": owner_1,
			"start_time": now - timedelta(days=4),
			"end_time": now - timedelta(days=4) + timedelta(seconds=540),
			"reference_doctype": "CRM Lead",
			"reference_docname": lead_names[1],
		},
		{
			"type": "Outgoing",
			"status": "No Answer",
			"telephony_medium": "Manual",
			"duration": 0,
			"from": rep_numbers[owner_1],
			"to": "+1 555 000 5678",
			"caller": owner_1,
			"start_time": now - timedelta(days=1),
			"end_time": now - timedelta(days=1),
			"reference_doctype": "CRM Lead",
			"reference_docname": lead_names[1],
		},
		{
			"type": "Outgoing",
			"status": "Completed",
			"telephony_medium": "Manual",
			"duration": 420,
			"from": rep_numbers[owner_2],
			"to": "+1 555 000 9012",
			"caller": owner_2,
			"start_time": now - timedelta(days=3),
			"end_time": now - timedelta(days=3) + timedelta(seconds=420),
			"reference_doctype": "CRM Lead",
			"reference_docname": lead_names[2],
		},
		{
			"type": "Incoming",
			"status": "Completed",
			"telephony_medium": "Manual",
			"duration": 600,
			"from": "+1 555 000 3456",
			"to": rep_numbers[owner_1],
			"receiver": owner_1,
			"start_time": now - timedelta(days=6),
			"end_time": now - timedelta(days=6) + timedelta(seconds=600),
			"reference_doctype": "CRM Lead",
			"reference_docname": lead_names[3],
		},
	]

	created = []
	for data in call_logs_data:
		log_owner = data.get("caller") or data.get("receiver") or frappe.session.user
		log_ts = data.get("start_time")
		log = frappe.get_doc(
			{"doctype": "CRM Call Log", "id": frappe.generate_hash(length=10), **data}
		).insert(ignore_permissions=True)
		patch = {"owner": log_owner, "modified_by": log_owner}
		if log_ts:
			patch["creation"] = log_ts
			patch["modified"] = log_ts
		frappe.db.set_value("CRM Call Log", log.name, patch, update_modified=False)
		created.append(log.name)

	return created


def delete_demo_call_logs(call_log_names):
	for name in call_log_names:
		if frappe.db.exists("CRM Call Log", name):
			frappe.delete_doc("CRM Call Log", name, ignore_permissions=True, force=True)
