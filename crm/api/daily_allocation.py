from __future__ import annotations

import json
from typing import Any

import frappe
from frappe import _


CRM_ADMIN_ROLES = {"System Manager", "Sales Manager", "Sales Master Manager"}

VALID_STATUSES = ["To Do", "In Progress", "Pending", "Callback", "Follow up", "Not Interested"]
LEGACY_STATUSES = ["Completed", "Follow-up Required"]

COUNTRY_TIMEZONE_MAP = {
	"india": "Asia/Kolkata",
	"singapore": "Asia/Singapore",
	"malaysia": "Asia/Kuala_Lumpur",
	"australia": "Australia/Sydney",
	"united kingdom": "Europe/London",
	"uk": "Europe/London",
	"great britain": "Europe/London",
	"united states": "America/New_York",
	"united states of america": "America/New_York",
	"usa": "America/New_York",
	"us": "America/New_York",
	"canada": "America/Toronto",
	"germany": "Europe/Berlin",
	"france": "Europe/Paris",
	"italy": "Europe/Rome",
	"spain": "Europe/Madrid",
	"netherlands": "Europe/Amsterdam",
	"belgium": "Europe/Brussels",
	"switzerland": "Europe/Zurich",
	"sweden": "Europe/Stockholm",
	"norway": "Europe/Oslo",
	"denmark": "Europe/Copenhagen",
	"finland": "Europe/Helsinki",
	"ireland": "Europe/Dublin",
	"poland": "Europe/Warsaw",
	"austria": "Europe/Vienna",
	"portugal": "Europe/Lisbon",
	"greece": "Europe/Athens",
	"turkey": "Europe/Istanbul",
	"russia": "Europe/Moscow",
	"united arab emirates": "Asia/Dubai",
	"uae": "Asia/Dubai",
	"saudi arabia": "Asia/Riyadh",
	"qatar": "Asia/Qatar",
	"kuwait": "Asia/Kuwait",
	"bahrain": "Asia/Bahrain",
	"oman": "Asia/Muscat",
	"japan": "Asia/Tokyo",
	"china": "Asia/Shanghai",
	"hong kong": "Asia/Hong_Kong",
	"taiwan": "Asia/Taipei",
	"south korea": "Asia/Seoul",
	"indonesia": "Asia/Jakarta",
	"philippines": "Asia/Manila",
	"thailand": "Asia/Bangkok",
	"vietnam": "Asia/Ho_Chi_Minh",
	"new zealand": "Pacific/Auckland",
	"south africa": "Africa/Johannesburg",
	"egypt": "Africa/Cairo",
	"nigeria": "Africa/Lagos",
	"kenya": "Africa/Nairobi",
	"brazil": "America/Sao_Paulo",
	"mexico": "America/Mexico_City",
	"argentina": "America/Argentina/Buenos_Aires",
	"chile": "America/Santiago",
	"colombia": "America/Bogota",
	"peru": "America/Lima",
	"bangladesh": "Asia/Dhaka",
	"pakistan": "Asia/Karachi",
	"sri lanka": "Asia/Colombo",
	"nepal": "Asia/Kathmandu",
	"israel": "Asia/Jerusalem",
}

TZ_ABBR_OVERRIDES = {
	"Asia/Singapore": "SGT",
	"Asia/Kuala_Lumpur": "MYT",
	"Asia/Dubai": "GST",
	"Asia/Hong_Kong": "HKT",
	"Asia/Bangkok": "ICT",
	"Asia/Jakarta": "WIB",
	"Asia/Manila": "PHT",
	"Asia/Riyadh": "AST",
	"Africa/Johannesburg": "SAST",
	"Asia/Shanghai": "CST",
	"Asia/Tokyo": "JST",
	"Asia/Seoul": "KST",
}


def format_timezone_label(tz_str: str | None, country: str | None = None) -> str:
	"""Convert IANA or raw timezone to user-friendly DST-aware string e.g. 'GMT+5:30 (IST)'."""
	if not tz_str or tz_str == "Not Available":
		if country:
			tz_str = get_timezone_for_country(country)
	if not tz_str or tz_str == "Not Available":
		return "Not Available"

	if str(tz_str).startswith("GMT"):
		return str(tz_str)

	try:
		from datetime import datetime
		from zoneinfo import ZoneInfo

		now_dt = datetime.now(ZoneInfo(tz_str))
		offset = now_dt.utcoffset()
		if offset is None:
			return tz_str

		total_seconds = int(offset.total_seconds())
		sign = "+" if total_seconds >= 0 else "-"
		abs_seconds = abs(total_seconds)
		hours = abs_seconds // 3600
		minutes = (abs_seconds % 3600) // 60
		gmt_str = f"GMT{sign}{hours}:{minutes:02d}" if minutes > 0 else f"GMT{sign}{hours}"

		abbr = TZ_ABBR_OVERRIDES.get(tz_str)
		if not abbr:
			tzname = now_dt.tzname()
			if tzname and not (tzname.startswith(("+", "-")) or tzname.isdigit()):
				abbr = tzname

		return f"{gmt_str} ({abbr})" if abbr else gmt_str
	except Exception:
		return str(tz_str)


def get_timezone_for_country(country: str | None) -> str:
	"""Derive primary IANA timezone from country identifier."""
	if not country:
		return "Not Available"
	cleaned = country.strip().lower()
	if cleaned in COUNTRY_TIMEZONE_MAP:
		return COUNTRY_TIMEZONE_MAP[cleaned]
	for c_key, c_tz in COUNTRY_TIMEZONE_MAP.items():
		if c_key in cleaned or cleaned in c_key:
			return c_tz
	return "Not Available"


def resolve_country_for_contact(contact_name: str, org_name: str | None = None) -> str | None:
	"""Retrieve country from linked Address record via Contact or Organization."""
	if not contact_name:
		return None
	# 1. Address directly linked to Contact
	country_res = frappe.db.sql("""
		SELECT a.country FROM `tabAddress` a
		JOIN `tabDynamic Link` dl ON dl.parent = a.name
		WHERE dl.link_doctype = 'Contact' AND dl.link_name = %s AND (a.country IS NOT NULL AND a.country != '')
		ORDER BY a.creation desc LIMIT 1
	""", contact_name)
	if country_res and country_res[0][0]:
		return country_res[0][0]

	# 2. Address linked to Organization
	if org_name:
		country_res = frappe.db.sql("""
			SELECT a.country FROM `tabAddress` a
			JOIN `tabDynamic Link` dl ON dl.parent = a.name
			WHERE dl.link_doctype = 'CRM Organization' AND dl.link_name = %s AND (a.country IS NOT NULL AND a.country != '')
			ORDER BY a.creation desc LIMIT 1
		""", org_name)
		if country_res and country_res[0][0]:
			return country_res[0][0]

	return None


def is_admin_user(user: str | None = None) -> bool:
	"""Check if the user is an Administrator or has Admin/Manager roles in CRM."""
	if not user:
		user = frappe.session.user
	if user == "Administrator":
		return True
	user_roles = set(frappe.get_roles(user))
	return bool(user_roles.intersection(CRM_ADMIN_ROLES))


@frappe.whitelist()
def get_daily_allocation_summary(date: str | None = None) -> dict[str, Any]:
	"""Return daily allocation summary counts for a given date.
	
	Admins receive aggregate numbers across all active users plus a per-user breakdown.
	Standard users receive ONLY their own counts for that date.
	"""
	allocation_date = date or frappe.utils.today()
	current_user = frappe.session.user
	is_admin = is_admin_user(current_user)

	if not is_admin:
		# Standard user: strictly return own metrics
		tasks = frappe.get_all(
			"CRM Daily Allocation",
			filters={"assigned_to": current_user, "allocation_date": allocation_date},
			fields=["status"],
		)
		total = len(tasks)
		to_do = sum(1 for t in tasks if t.status == "To Do")
		in_progress = sum(1 for t in tasks if t.status == "In Progress")
		pending = sum(1 for t in tasks if t.status == "Pending")
		callback = sum(1 for t in tasks if t.status == "Callback")
		follow_up = sum(1 for t in tasks if t.status in ("Follow up", "Follow-up Required"))
		not_interested = sum(1 for t in tasks if t.status == "Not Interested")
		completed = sum(1 for t in tasks if t.status == "Completed")

		return {
			"is_admin": False,
			"date": str(allocation_date),
			"user": current_user,
			"total_tasks": total,
			"to_do": to_do,
			"in_progress": in_progress,
			"pending": pending,
			"callback": callback,
			"follow_up": follow_up,
			"not_interested": not_interested,
			"completed": completed,
			"users": [],
		}

	# Admin path: retrieve all active assignable users and their allocations
	assignable_users = get_assignable_users()
	all_allocations = frappe.get_all(
		"CRM Daily Allocation",
		filters={"allocation_date": allocation_date},
		fields=["name", "assigned_to", "status"],
	)

	# Aggregate per user
	user_stats = {}
	for u in assignable_users:
		user_stats[u["name"]] = {
			"user": u["name"],
			"full_name": u["full_name"],
			"email": u["email"],
			"user_image": u.get("user_image"),
			"total": 0,
			"to_do": 0,
			"in_progress": 0,
			"pending": 0,
			"callback": 0,
			"follow_up": 0,
			"not_interested": 0,
			"completed": 0,
		}

	total_tasks = len(all_allocations)
	tot_to_do = 0
	tot_in_progress = 0
	tot_pending = 0
	tot_callback = 0
	tot_follow_up = 0
	tot_not_interested = 0
	tot_completed = 0

	for alloc in all_allocations:
		assigned_user = alloc.assigned_to
		st = alloc.status or "To Do"

		if st == "To Do":
			tot_to_do += 1
		elif st == "In Progress":
			tot_in_progress += 1
		elif st == "Callback":
			tot_callback += 1
		elif st in ("Follow up", "Follow-up Required"):
			tot_follow_up += 1
		elif st == "Not Interested":
			tot_not_interested += 1
		elif st == "Completed":
			tot_completed += 1
		else:
			tot_pending += 1

		if assigned_user in user_stats:
			user_stats[assigned_user]["total"] += 1
			if st == "To Do":
				user_stats[assigned_user]["to_do"] += 1
			elif st == "In Progress":
				user_stats[assigned_user]["in_progress"] += 1
			elif st == "Callback":
				user_stats[assigned_user]["callback"] += 1
			elif st in ("Follow up", "Follow-up Required"):
				user_stats[assigned_user]["follow_up"] += 1
			elif st == "Not Interested":
				user_stats[assigned_user]["not_interested"] += 1
			elif st == "Completed":
				user_stats[assigned_user]["completed"] += 1
			else:
				user_stats[assigned_user]["pending"] += 1
		else:
			# If user was assigned in DB but not in current active user list
			user_full_name = frappe.db.get_value("User", assigned_user, "full_name") or assigned_user
			user_stats[assigned_user] = {
				"user": assigned_user,
				"full_name": user_full_name,
				"email": assigned_user,
				"user_image": None,
				"total": 1,
				"to_do": 1 if st == "To Do" else 0,
				"in_progress": 1 if st == "In Progress" else 0,
				"pending": 1 if st == "Pending" else 0,
				"callback": 1 if st == "Callback" else 0,
				"follow_up": 1 if st in ("Follow up", "Follow-up Required") else 0,
				"not_interested": 1 if st == "Not Interested" else 0,
				"completed": 1 if st == "Completed" else 0,
			}

	return {
		"is_admin": True,
		"date": str(allocation_date),
		"total_users": len(assignable_users),
		"total_tasks": total_tasks,
		"to_do": tot_to_do,
		"in_progress": tot_in_progress,
		"pending": tot_pending,
		"callback": tot_callback,
		"follow_up": tot_follow_up,
		"not_interested": tot_not_interested,
		"completed": tot_completed,
		"users": list(user_stats.values()),
	}


@frappe.whitelist()
def get_allocated_tasks(
	date: str | None = None,
	user: str | None = None,
	status: str | None = None,
	search: str | None = None,
) -> list[dict[str, Any]]:
	"""Return task details.
	
	Standard users are strictly restricted to their own tasks.
	Admin users can inspect any user's tasks or all tasks for the given date.
	"""
	current_user = frappe.session.user
	is_admin = is_admin_user(current_user)

	filters = {}

	# Date filter: default to date provided (if provided)
	if date:
		filters["allocation_date"] = date

	# User permission check & filtering
	if not is_admin:
		if user and user != current_user:
			frappe.throw(_("Permission denied. You can only view your own tasks."), frappe.PermissionError)
		filters["assigned_to"] = current_user
	else:
		if user and user not in ("all", "*"):
			filters["assigned_to"] = user

	if status and status not in ("all", "*"):
		filters["status"] = status

	query = frappe.get_all(
		"CRM Daily Allocation",
		filters=filters,
		fields=[
			"name",
			"assigned_to",
			"allocated_by",
			"allocation_date",
			"status",
			"contact",
			"contact_name",
			"organization",
			"email",
			"mobile_no",
			"country",
			"timezone",
			"notes",
			"follow_up_date",
			"creation",
			"modified",
		],
		order_by="modified desc, creation desc",
	)

	# Cache user names for display
	user_names = {}

	results = []
	search_lower = (search or "").strip().lower()

	for row in query:
		# Search filter on text fields
		if search_lower:
			fields_to_search = [
				row.contact_name or "",
				row.organization or "",
				row.email or "",
				row.mobile_no or "",
				row.country or "",
				row.timezone or "",
				row.notes or "",
				row.status or "",
			]
			if not any(search_lower in f.lower() for f in fields_to_search):
				continue

		assigned_id = row.assigned_to
		if assigned_id not in user_names:
			user_names[assigned_id] = frappe.db.get_value("User", assigned_id, "full_name") or assigned_id

		alloc_by_id = row.allocated_by
		if alloc_by_id not in user_names:
			user_names[alloc_by_id] = frappe.db.get_value("User", alloc_by_id, "full_name") or alloc_by_id

		# Country and Timezone resolution
		c_val = row.get("country")
		if not c_val:
			c_val = resolve_country_for_contact(row.contact, row.organization)
		display_country = c_val or "Not Available"

		tz_val = row.get("timezone")
		if not tz_val or tz_val == "Not Available":
			tz_val = get_timezone_for_country(c_val) if c_val else "Not Available"
		display_timezone = format_timezone_label(tz_val, c_val)

		# Clean status mapping
		st_val = row.status or "To Do"
		if st_val == "Follow-up Required":
			st_val = "Follow up"
		elif st_val == "Completed":
			st_val = "To Do"
		elif st_val not in VALID_STATUSES:
			st_val = "To Do"

		results.append({
			"name": str(row.name),
			"contact": row.contact,
			"contact_name": row.contact_name or row.contact,
			"prospect_name": row.contact_name or row.contact,
			"organization": row.organization or "",
			"email": row.email or "",
			"mobile_no": row.mobile_no or "",
			"country": display_country,
			"timezone": display_timezone,
			"raw_timezone": tz_val or "",
			"allocation_date": str(row.allocation_date),
			"assigned_to": row.assigned_to,
			"assigned_to_name": user_names[assigned_id],
			"allocated_by": row.allocated_by,
			"allocated_by_name": user_names[alloc_by_id],
			"status": st_val,
			"notes": row.notes or "",
			"follow_up_date": str(row.follow_up_date) if row.follow_up_date else "",
			"creation": str(row.creation),
			"modified": str(row.modified),
		})

	return results


def sync_contact_daily_allocation(
	contact_name: str,
	assigned_to: str,
	allocated_by: str | None = None,
	allocation_date: str | None = None,
	status: str = "To Do",
) -> Any:
	"""Automatically create or update the CRM Daily Allocation task when a Contact is assigned.

	Ensures:
	- No duplicate tasks: if an allocation already exists for this contact, update it.
	- Reassigning updates the existing task record, sets assigned_to to the new user, and status to 'To Do'.
	- Resolves organization, email, mobile_no, country, and timezone from the contact.
	- Sets allocation_date (defaults to today).
	- Emits realtime socket event so My Tasks and Contacts lists refresh automatically without browser reload.
	"""
	if not contact_name or not frappe.db.exists("Contact", contact_name):
		return None

	contact_doc = frappe.get_doc("Contact", contact_name)

	# 1. Resolve contact details
	full_name = (
		contact_doc.full_name
		or f"{contact_doc.first_name or ''} {contact_doc.last_name or ''}".strip()
		or contact_name
	)
	c_email = (
		contact_doc.email_id
		or (contact_doc.email_ids[0].email_id if contact_doc.email_ids else "")
		or ""
	)
	c_phone = (
		contact_doc.mobile_no
		or (contact_doc.phone_nos[0].phone if contact_doc.phone_nos else "")
		or ""
	)

	# Organization resolution
	org_name = contact_doc.company_name or ""
	if not org_name and contact_doc.links:
		for l in contact_doc.links:
			if l.link_doctype == "CRM Organization":
				org_name = l.link_name
				break

	# Country and Timezone resolution
	cntry = resolve_country_for_contact(contact_name, org_name)
	tz = get_timezone_for_country(cntry) if cntry else "Not Available"

	alloc_date = allocation_date or frappe.utils.today()
	allocator = allocated_by or frappe.session.user or "Administrator"

	# 2. Check existing allocation records for this contact (prevent duplicates!)
	existing_tasks = frappe.get_all(
		"CRM Daily Allocation",
		filters={"contact": contact_name},
		fields=["name", "assigned_to", "status"],
		order_by="modified desc",
	)

	alloc_doc = None
	if existing_tasks:
		# Update the primary existing record
		primary_name = existing_tasks[0]["name"]
		alloc_doc = frappe.get_doc("CRM Daily Allocation", primary_name)
		alloc_doc.assigned_to = assigned_to
		alloc_doc.allocated_by = allocator
		alloc_doc.allocation_date = alloc_date
		alloc_doc.status = status or "To Do"
		alloc_doc.contact_name = full_name
		alloc_doc.organization = org_name
		alloc_doc.email = c_email
		alloc_doc.mobile_no = c_phone
		alloc_doc.country = cntry or ""
		alloc_doc.timezone = tz if tz != "Not Available" else ""
		alloc_doc.flags.ignore_permissions = True
		alloc_doc.save()

		# Delete any redundant duplicates if they exist in DB
		if len(existing_tasks) > 1:
			for redundant in existing_tasks[1:]:
				frappe.delete_doc(
					"CRM Daily Allocation", redundant["name"], force=True, ignore_permissions=True
				)
	else:
		# Create new task
		alloc_doc = frappe.new_doc("CRM Daily Allocation")
		alloc_doc.assigned_to = assigned_to
		alloc_doc.allocated_by = allocator
		alloc_doc.allocation_date = alloc_date
		alloc_doc.status = status or "To Do"
		alloc_doc.contact = contact_name
		alloc_doc.contact_name = full_name
		alloc_doc.organization = org_name
		alloc_doc.email = c_email
		alloc_doc.mobile_no = c_phone
		alloc_doc.country = cntry or ""
		alloc_doc.timezone = tz if tz != "Not Available" else ""
		alloc_doc.flags.ignore_permissions = True
		alloc_doc.insert()

	# 3. Synchronize Contact._assign so it reflects only this assignee
	try:
		frappe.db.set_value(
			"Contact",
			contact_name,
			{
				"_assign": json.dumps([assigned_to]),
				"custom_is_dropped": 0,
			},
			update_modified=False,
		)
	except Exception:
		pass

	# 4. Publish realtime event for automatic UI update without browser refresh
	try:
		payload = {
			"user": assigned_to,
			"contact": contact_name,
			"allocation_date": str(alloc_date),
			"task_id": alloc_doc.name,
		}
		frappe.publish_realtime("crm_tasks_updated", payload, after_commit=True)
	except Exception:
		pass

	return alloc_doc


def clear_contact_daily_allocation(contact_name: str) -> None:
	"""Remove allocation tasks when a Contact is unassigned or marked dropped."""
	if not contact_name:
		return
	frappe.db.delete("CRM Daily Allocation", {"contact": contact_name})
	try:
		frappe.publish_realtime(
			"crm_tasks_updated",
			{"contact": contact_name, "cleared": True},
			after_commit=True,
		)
	except Exception:
		pass


def sync_contact_assignment_to_user(contact_name: str, new_user: str) -> None:
	"""Synchronize Contact _assign and ToDo records when reassigned."""
	if not contact_name or not frappe.db.exists("Contact", contact_name):
		return

	# 1. Update Contact._assign
	frappe.db.set_value(
		"Contact",
		contact_name,
		{
			"_assign": json.dumps([new_user]),
			"custom_is_dropped": 0,
		},
		update_modified=False,
	)

	# 2. Cancel old open ToDos for other users
	old_todos = frappe.get_all(
		"ToDo",
		filters={
			"reference_type": "Contact",
			"reference_name": contact_name,
			"status": "Open",
			"allocated_to": ["!=", new_user],
		},
		pluck="name",
	)
	for ot in old_todos:
		frappe.db.set_value("ToDo", ot, "status", "Cancelled")

	# 3. Ensure an open ToDo exists for new_user
	existing_todo = frappe.db.get_value(
		"ToDo",
		{
			"reference_type": "Contact",
			"reference_name": contact_name,
			"allocated_to": new_user,
			"status": "Open",
		},
		"name",
	)
	if not existing_todo:
		new_todo = frappe.new_doc("ToDo")
		new_todo.reference_type = "Contact"
		new_todo.reference_name = contact_name
		new_todo.allocated_to = new_user
		new_todo.assigned_by = frappe.session.user
		new_todo.status = "Open"
		new_todo.date = frappe.utils.today()
		new_todo.description = _("Assignment for Contact {0}").format(contact_name)
		new_todo.flags.ignore_permissions = True
		new_todo.insert()


@frappe.whitelist()
def allocate_prospects(
	assigned_to: str,
	contacts: Any,
	allocation_date: str | None = None,
	force: bool | int = False,
) -> dict[str, Any]:
	"""Assign prospects/contacts to a user for a given date.
	
	Only Admins can perform allocations. Duplicate allocation for the same user
	on the same date is prevented unless force=True.
	"""
	if not is_admin_user():
		frappe.throw(_("Only Admin can allocate prospects to users."), frappe.PermissionError)

	if not assigned_to:
		frappe.throw(_("Please select a user to assign."))

	if not frappe.db.exists("User", assigned_to):
		frappe.throw(_("Selected user {0} does not exist.").format(assigned_to))

	alloc_date = allocation_date or frappe.utils.today()

	if isinstance(contacts, str):
		try:
			contacts = json.loads(contacts)
		except Exception:
			contacts = [c.strip() for c in contacts.split(",") if c.strip()]

	if not contacts:
		frappe.throw(_("Please select at least one prospect to allocate."))

	# Duplicate prevention
	existing_allocated = set(
		frappe.get_all(
			"CRM Daily Allocation",
			filters={
				"assigned_to": assigned_to,
				"allocation_date": alloc_date,
				"contact": ["in", contacts],
			},
			pluck="contact",
		)
	)

	allocated = []
	skipped = []

	current_admin = frappe.session.user

	for c_id in contacts:
		if c_id in existing_allocated and not force:
			skipped.append(c_id)
			continue

		if not frappe.db.exists("Contact", c_id):
			continue

		alloc_doc = sync_contact_daily_allocation(
			contact_name=c_id,
			assigned_to=assigned_to,
			allocated_by=current_admin,
			allocation_date=alloc_date,
			status="To Do",
		)
		sync_contact_assignment_to_user(c_id, assigned_to)

		allocated.append({
			"name": alloc_doc.name,
			"contact": c_id,
			"contact_name": alloc_doc.contact_name,
			"country": alloc_doc.country or "Not Available",
			"timezone": format_timezone_label(alloc_doc.timezone, alloc_doc.country),
			"assigned_to": assigned_to,
			"allocation_date": str(alloc_date),
		})

	frappe.db.commit()

	return {
		"success": True,
		"allocated_count": len(allocated),
		"skipped_count": len(skipped),
		"allocated": allocated,
		"skipped": skipped,
		"message": _("Successfully allocated {0} prospect(s) to {1} for {2}.").format(
			len(allocated),
			frappe.db.get_value("User", assigned_to, "full_name") or assigned_to,
			alloc_date,
		),
	}


@frappe.whitelist()
def update_task_status(
	task_name: str | int,
	status: str,
	notes: str | None = None,
	follow_up_date: str | None = None,
) -> dict[str, Any]:
	"""Update task status and notes.
	
	Users can update only their own tasks.
	Users cannot alter assigned_to or allocation_date.
	"""
	if not frappe.db.exists("CRM Daily Allocation", task_name):
		frappe.throw(_("Task {0} not found.").format(task_name), frappe.DoesNotExistError)

	doc = frappe.get_doc("CRM Daily Allocation", task_name)
	current_user = frappe.session.user
	is_admin = is_admin_user(current_user)

	if not is_admin and doc.assigned_to != current_user:
		frappe.throw(_("Permission denied. You can only update your own assigned tasks."), frappe.PermissionError)

	allowed_statuses = set(VALID_STATUSES) | set(LEGACY_STATUSES)
	if status not in allowed_statuses:
		frappe.throw(_("Invalid status {0}. Allowed: {1}").format(status, ", ".join(VALID_STATUSES)))

	doc.status = status
	if notes is not None:
		doc.notes = notes
	if follow_up_date is not None:
		doc.follow_up_date = follow_up_date or None

	doc.flags.ignore_permissions = True
	doc.save()
	frappe.db.commit()

	return {
		"success": True,
		"name": doc.name,
		"status": doc.status,
		"notes": doc.notes,
		"follow_up_date": str(doc.follow_up_date) if doc.follow_up_date else "",
	}


@frappe.whitelist()
def reassign_task(
	task_name: str | int,
	new_user: str,
	new_date: str | None = None,
) -> dict[str, Any]:
	"""Reassign a task to another user or date (Admin only)."""
	if not is_admin_user():
		frappe.throw(_("Only Admin can reassign tasks."), frappe.PermissionError)

	if not frappe.db.exists("CRM Daily Allocation", task_name):
		frappe.throw(_("Task {0} not found.").format(task_name), frappe.DoesNotExistError)

	if not frappe.db.exists("User", new_user):
		frappe.throw(_("User {0} does not exist.").format(new_user))

	doc = frappe.get_doc("CRM Daily Allocation", task_name)
	doc.assigned_to = new_user
	if new_date:
		doc.allocation_date = new_date

	doc.flags.ignore_permissions = True
	doc.save()

	# Synchronize Contact assignment
	if doc.contact and frappe.db.exists("Contact", doc.contact):
		sync_contact_assignment_to_user(doc.contact, new_user)

	frappe.db.commit()

	try:
		frappe.publish_realtime(
			"crm_tasks_updated",
			{"user": new_user, "task_id": doc.name, "contact": doc.contact},
			after_commit=True,
		)
	except Exception:
		pass

	return {"success": True, "name": doc.name, "assigned_to": doc.assigned_to, "allocation_date": str(doc.allocation_date)}


@frappe.whitelist()
def delete_allocation(task_name: str | int) -> dict[str, Any]:
	"""Delete an allocation record (Admin only)."""
	if not is_admin_user():
		frappe.throw(_("Only Admin can delete allocations."), frappe.PermissionError)

	if not frappe.db.exists("CRM Daily Allocation", task_name):
		frappe.throw(_("Task {0} not found.").format(task_name), frappe.DoesNotExistError)

	contact_name = frappe.db.get_value("CRM Daily Allocation", task_name, "contact")
	frappe.delete_doc("CRM Daily Allocation", task_name, force=True, ignore_permissions=True)
	if contact_name and frappe.db.exists("Contact", contact_name):
		from frappe.desk.form import assign_to
		try:
			assign_to.clear("Contact", contact_name, ignore_permissions=True)
		except Exception:
			pass
		frappe.db.set_value("Contact", contact_name, "_assign", None, update_modified=False)

	frappe.db.commit()
	try:
		frappe.publish_realtime("crm_tasks_updated", {"cleared": True}, after_commit=True)
	except Exception:
		pass

	return {"success": True, "message": _("Allocation removed.")}


@frappe.whitelist()
def get_available_contacts(
	search: str | None = None,
	allocation_date: str | None = None,
	assigned_to: str | None = None,
) -> list[dict[str, Any]]:
	"""Return real CRM contacts/prospects available for allocation (Admin only).
	
	Filters out system user contacts, dropped contacts, and provides allocation status.
	"""
	if not is_admin_user():
		frappe.throw(_("Only Admin can view available prospects."), frappe.PermissionError)

	alloc_date = allocation_date or frappe.utils.today()

	# Find contacts already allocated on alloc_date
	allocated_query = frappe.get_all(
		"CRM Daily Allocation",
		filters={"allocation_date": alloc_date},
		fields=["contact", "assigned_to"],
	)
	allocated_map = {row.contact: row.assigned_to for row in allocated_query}

	# Query contacts (exclude internal system user contacts and dropped contacts)
	contacts = frappe.db.sql("""
		SELECT name, first_name, last_name, full_name, company_name, email_id, mobile_no, user
		FROM `tabContact`
		WHERE (custom_is_dropped = 0 OR custom_is_dropped IS NULL)
		  AND (user IS NULL OR user = '')
		ORDER BY creation desc
		LIMIT 200
	""", as_dict=True)

	results = []
	search_lower = search.lower().strip() if search else None

	for c in contacts:
		full_name = c.full_name or f"{c.first_name or ''} {c.last_name or ''}".strip() or c.name

		if search_lower:
			fields_to_search = [
				full_name,
				c.first_name or "",
				c.last_name or "",
				c.company_name or "",
				c.email_id or "",
				c.mobile_no or "",
			]
			if not any(search_lower in f.lower() for f in fields_to_search):
				continue

		allocated_user = allocated_map.get(c.name)
		allocated_user_name = (
			frappe.db.get_value("User", allocated_user, "full_name") if allocated_user else None
		)

		results.append({
			"name": c.name,
			"full_name": full_name,
			"organization": c.company_name or "",
			"email": c.email_id or "",
			"mobile_no": c.mobile_no or "",
			"is_allocated": bool(allocated_user),
			"allocated_to": allocated_user,
			"allocated_to_name": allocated_user_name,
			"is_allocated_to_target": (allocated_user == assigned_to) if assigned_to else False,
		})

	return results


@frappe.whitelist()
def get_assignable_users() -> list[dict[str, Any]]:
	"""Return active CRM users eligible to receive daily task allocations."""
	# Fetch all users with CRM roles
	from crm.api.session import CRM_ALLOWED_ROLES

	user_names = frappe.get_all(
		"Has Role",
		filters={"parenttype": "User", "role": ["in", CRM_ALLOWED_ROLES]},
		pluck="parent",
		distinct=True,
	)

	users = frappe.get_all(
		"User",
		filters={"name": ["in", list(user_names)], "enabled": 1, "user_type": "System User"},
		fields=["name", "full_name", "email", "user_image"],
		order_by="full_name asc",
	)

	# Clean & ensure non-null full names
	result = []
	for u in users:
		result.append({
			"name": u.name,
			"full_name": u.full_name or u.name.split("@")[0],
			"email": u.email or u.name,
			"user_image": u.user_image,
		})

	return result


# ==============================================================================
# PROSPECT & LEAD LINKING HELPERS
# ==============================================================================

def resolve_lead_for_contact(contact_name: str) -> str | None:
	"""Retrieve or locate the corresponding CRM Lead name for a given Contact."""
	if not contact_name or not frappe.db.exists("Contact", contact_name):
		return None

	c_doc = frappe.get_doc("Contact", contact_name)

	# 0. Check Dynamic Links
	for link in getattr(c_doc, "links", []) or []:
		if link.link_doctype == "CRM Lead" and frappe.db.exists("CRM Lead", link.link_name):
			return link.link_name

	# 1. Search by email address
	emails = [c_doc.email_id] if getattr(c_doc, "email_id", None) else []
	if getattr(c_doc, "email_ids", None):
		emails.extend([e.email_id for e in c_doc.email_ids if e.email_id])
	for em in emails:
		if em:
			lead_name = frappe.db.get_value("CRM Lead", {"email": em}, "name")
			if lead_name:
				return lead_name

	# 2. Search by mobile/phone number
	phones = [c_doc.mobile_no, c_doc.phone]
	if c_doc.phone_nos:
		phones.extend([p.phone for p in c_doc.phone_nos if p.phone])
	for ph in phones:
		if ph:
			lead_name = frappe.db.get_value("CRM Lead", {"mobile_no": ph}, "name") or frappe.db.get_value("CRM Lead", {"phone": ph}, "name")
			if lead_name:
				return lead_name

	# 3. Search by name & organization
	filters = {}
	if c_doc.first_name:
		filters["first_name"] = c_doc.first_name
	if c_doc.last_name:
		filters["last_name"] = c_doc.last_name
	if c_doc.company_name:
		filters["organization"] = c_doc.company_name
	if filters:
		lead_name = frappe.db.get_value("CRM Lead", filters, "name")
		if lead_name:
			return lead_name

	return None


# ==============================================================================
# AUTOMATIC WORKFLOW: TO DO -> IN PROGRESS ON OUTGOING EMAIL / COMPLETED CALL
# ==============================================================================

def check_and_advance_task_to_in_progress(
	contact: str | None = None,
	lead: str | None = None,
	email: str | None = None,
	phone: str | None = None,
):
	"""Automatically transition an allocated task from 'To Do' to 'In Progress' upon activity.

	Triggers ONLY for:
	- Successfully sent outgoing email.
	- Successfully completed phone call.

	CRITICAL RULES:
	- If the task is currently 'To Do', transition to 'In Progress'.
	- If the task is already 'In Progress', 'Completed', 'Callback', 'Follow up', or 'Not Interested',
	  do NOT overwrite that status automatically.
	- Opening/viewing contact details does NOT trigger this transition.
	"""
	if not (contact or lead or email or phone):
		return

	contact_names = set()
	if contact:
		contact_names.add(contact)

	# If lead provided, find linked contact name & contact details
	if lead and frappe.db.exists("CRM Lead", lead):
		lead_doc = frappe.get_doc("CRM Lead", lead)
		if lead_doc.email and not email:
			email = lead_doc.email
		if lead_doc.mobile_no and not phone:
			phone = lead_doc.mobile_no

	if email:
		c_by_email = frappe.db.get_value("Contact Email", {"email_id": email}, "parent") or frappe.db.get_value("Contact", {"email_id": email}, "name")
		if c_by_email:
			contact_names.add(c_by_email)

	if phone:
		c_by_phone = frappe.db.get_value("Contact Phone", {"phone": phone}, "parent") or frappe.db.get_value("Contact", {"mobile_no": phone}, "name")
		if c_by_phone:
			contact_names.add(c_by_phone)

	matching_tasks = []

	if contact_names:
		matching_tasks = frappe.get_all(
			"CRM Daily Allocation",
			filters={"contact": ["in", list(contact_names)], "status": "To Do"},
			fields=["name", "contact", "status"],
		)

	if not matching_tasks and email:
		matching_tasks = frappe.get_all(
			"CRM Daily Allocation",
			filters={"email": email, "status": "To Do"},
			fields=["name", "contact", "status"],
		)

	if not matching_tasks and phone:
		matching_tasks = frappe.get_all(
			"CRM Daily Allocation",
			filters={"mobile_no": phone, "status": "To Do"},
			fields=["name", "contact", "status"],
		)

	for t in matching_tasks:
		frappe.db.set_value("CRM Daily Allocation", t["name"], "status", "In Progress")


def on_call_log_update(doc, method=None):
	"""Doc event hook for CRM Call Log: when a call is completed, advance To Do to In Progress."""
	if getattr(doc, "status", None) == "Completed":
		contact_ref = doc.reference_docname if doc.reference_doctype == "Contact" else None
		lead_ref = doc.reference_docname if doc.reference_doctype == "CRM Lead" else None
		phone_val = getattr(doc, "to", None) or getattr(doc, "from", None)
		check_and_advance_task_to_in_progress(contact=contact_ref, lead=lead_ref, phone=phone_val)


# ==============================================================================
# BULK ACTIONS BACKEND APIS
# ==============================================================================

PROSPECT_LEAD_STATUSES = ["New", "Contacted", "Nurture", "Qualified", "Converted", "Unqualified", "Junk"]


@frappe.whitelist()
def change_prospect_status(
	doctype: str,
	names: Any,
	status: str,
) -> dict[str, Any]:
	"""Bulk change Prospect/CRM Lead status for selected Contacts, Leads, or Tasks.

	This changes the CRM Lead record status (New, Contacted, Nurture, Qualified, Converted,
	Unqualified, Junk), NOT the My Task workflow status.
	"""
	if status not in PROSPECT_LEAD_STATUSES:
		frappe.throw(_("Invalid CRM Lead Status '{0}'. Allowed: {1}").format(status, ", ".join(PROSPECT_LEAD_STATUSES)))

	if isinstance(names, str):
		try:
			names = json.loads(names)
		except Exception:
			names = [n.strip() for n in names.split(",") if n.strip()]

	if not names:
		frappe.throw(_("Please select at least one record to update."))

	updated = 0
	skipped = 0
	errors = []

	for name in names:
		lead_name = None

		if doctype == "CRM Lead":
			lead_name = name
		elif doctype == "Contact":
			lead_name = resolve_lead_for_contact(name)
		elif doctype == "CRM Daily Allocation":
			task_doc = frappe.db.get_value("CRM Daily Allocation", name, ["contact", "email", "mobile_no"], as_dict=True)
			if task_doc:
				lead_name = resolve_lead_for_contact(task_doc.contact)
				if not lead_name and task_doc.email:
					lead_name = frappe.db.get_value("CRM Lead", {"email": task_doc.email}, "name")

		if lead_name and frappe.db.exists("CRM Lead", lead_name):
			try:
				lead_doc = frappe.get_doc("CRM Lead", lead_name)
				lead_doc.status = status
				status_type = frappe.get_cached_value("CRM Lead Status", status, "type")
				if status == "Converted":
					lead_doc.converted = 1
				else:
					lead_doc.converted = 0

				if status_type == "Lost" and not lead_doc.lost_reason:
					# Default lost reason so validation passes
					default_reason = frappe.db.get_value("CRM Lost Reason", {"name": "Poor Fit"}, "name") or frappe.db.get_value("CRM Lost Reason", {}, "name")
					if default_reason:
						lead_doc.lost_reason = default_reason
				elif status_type != "Lost":
					lead_doc.lost_reason = None
					lead_doc.lost_notes = None

				lead_doc.flags.ignore_permissions = True
				lead_doc.save()
				updated += 1
			except Exception as e:
				errors.append(f"{name}: {str(e)}")
		else:
			skipped += 1
			errors.append(f"{name}: No linked CRM Lead record found")

	frappe.db.commit()

	return {
		"success": True,
		"updated": updated,
		"skipped": skipped,
		"errors": errors,
		"status": status,
		"message": _("Updated CRM Lead status to '{0}' for {1} prospect(s).").format(status, updated),
	}


@frappe.whitelist()
def bulk_convert_to_deal(
	doctype: str,
	names: Any,
) -> dict[str, Any]:
	"""Convert selected Contacts, Leads, or Tasks into CRM Deals."""
	if isinstance(names, str):
		try:
			names = json.loads(names)
		except Exception:
			names = [n.strip() for n in names.split(",") if n.strip()]

	if not names:
		frappe.throw(_("Please select at least one record to convert."))

	from crm.fcrm.doctype.crm_lead.crm_lead import convert_to_deal

	converted = []
	errors = []

	for item in names:
		lead_name = None
		contact_name = None

		if doctype == "CRM Lead":
			lead_name = item
		elif doctype == "Contact":
			contact_name = item
			lead_name = resolve_lead_for_contact(item)
		elif doctype == "CRM Daily Allocation":
			task_data = frappe.db.get_value("CRM Daily Allocation", item, ["contact", "email"], as_dict=True)
			if task_data:
				contact_name = task_data.contact
				lead_name = resolve_lead_for_contact(contact_name)
				if not lead_name and task_data.email:
					lead_name = frappe.db.get_value("CRM Lead", {"email": task_data.email}, "name")

		# If Contact exists without lead, create a lead so standard convert_to_deal works
		if not lead_name and contact_name and frappe.db.exists("Contact", contact_name):
			c_doc = frappe.get_doc("Contact", contact_name)
			new_lead = frappe.new_doc("CRM Lead")
			new_lead.first_name = c_doc.first_name or contact_name
			new_lead.last_name = c_doc.last_name or ""
			new_lead.email = c_doc.email_id or (c_doc.email_ids[0].email_id if c_doc.email_ids else "")
			new_lead.mobile_no = c_doc.mobile_no or (c_doc.phone_nos[0].phone if c_doc.phone_nos else "")
			new_lead.organization = c_doc.company_name or ""
			new_lead.status = "Qualified"
			new_lead.flags.ignore_permissions = True
			new_lead.insert()
			lead_name = new_lead.name

		if lead_name and frappe.db.exists("CRM Lead", lead_name):
			try:
				deal_doc = convert_to_deal(lead=lead_name, existing_contact=contact_name, if_converted="Create")
				converted.append({
					"item": item,
					"lead": lead_name,
					"deal": getattr(deal_doc, "name", str(deal_doc)),
				})
			except Exception as e:
				errors.append(f"{item}: {str(e)}")
		else:
			errors.append(f"{item}: Unable to identify or create Lead for conversion")

	frappe.db.commit()

	return {
		"success": True,
		"converted": len(converted),
		"deals": converted,
		"errors": errors,
		"message": _("Successfully converted {0} record(s) to deal(s).").format(len(converted)),
	}


@frappe.whitelist()
def bulk_reassign_tasks(
	tasks: Any,
	new_user: str,
	new_date: str | None = None,
) -> dict[str, Any]:
	"""Reassign multiple tasks to another user (Admin only)."""
	if not is_admin_user():
		frappe.throw(_("Permission denied. Only Admin can assign or reassign tasks."), frappe.PermissionError)

	if not frappe.db.exists("User", new_user):
		frappe.throw(_("Target user {0} does not exist.").format(new_user))

	if isinstance(tasks, str):
		try:
			tasks = json.loads(tasks)
		except Exception:
			tasks = [t.strip() for t in tasks.split(",") if t.strip()]

	updated = 0
	for t_id in tasks:
		if frappe.db.exists("CRM Daily Allocation", t_id):
			doc = frappe.get_doc("CRM Daily Allocation", t_id)
			doc.assigned_to = new_user
			if new_date:
				doc.allocation_date = new_date
			doc.flags.ignore_permissions = True
			doc.save()
			if doc.contact:
				sync_contact_assignment_to_user(doc.contact, new_user)
			updated += 1

	frappe.db.commit()
	try:
		frappe.publish_realtime(
			"crm_tasks_updated",
			{"user": new_user, "updated": updated},
			after_commit=True,
		)
	except Exception:
		pass

	return {"success": True, "updated": updated, "message": _("Reassigned {0} task(s) to {1}.").format(updated, new_user)}


@frappe.whitelist()
def bulk_clear_task_assignments(tasks: Any) -> dict[str, Any]:
	"""Clear task allocations for selected tasks (Admin only)."""
	if not is_admin_user():
		frappe.throw(_("Permission denied. Only Admin can clear task assignments."), frappe.PermissionError)

	if isinstance(tasks, str):
		try:
			tasks = json.loads(tasks)
		except Exception:
			tasks = [t.strip() for t in tasks.split(",") if t.strip()]

	cleared = 0
	for t_id in tasks:
		if frappe.db.exists("CRM Daily Allocation", t_id):
			contact_name = frappe.db.get_value("CRM Daily Allocation", t_id, "contact")
			frappe.delete_doc("CRM Daily Allocation", t_id, force=True, ignore_permissions=True)
			if contact_name and frappe.db.exists("Contact", contact_name):
				from frappe.desk.form import assign_to
				try:
					assign_to.clear("Contact", contact_name, ignore_permissions=True)
				except Exception:
					pass
				frappe.db.set_value("Contact", contact_name, "_assign", None, update_modified=False)
			cleared += 1

	frappe.db.commit()
	try:
		frappe.publish_realtime("crm_tasks_updated", {"cleared": cleared}, after_commit=True)
	except Exception:
		pass

	return {"success": True, "cleared": cleared, "message": _("Cleared assignment for {0} task(s).").format(cleared)}


@frappe.whitelist()
def bulk_delete_tasks(tasks: Any) -> dict[str, Any]:
	"""Delete selected task allocations (Admin only)."""
	from crm.api.security import is_admin_only
	if not is_admin_only():
		frappe.throw(_("Permission denied. Only Administrator can delete tasks."), frappe.PermissionError)

	if isinstance(tasks, str):
		try:
			tasks = json.loads(tasks)
		except Exception:
			tasks = [t.strip() for t in tasks.split(",") if t.strip()]

	deleted = 0
	for t_id in tasks:
		if frappe.db.exists("CRM Daily Allocation", t_id):
			contact_name = frappe.db.get_value("CRM Daily Allocation", t_id, "contact")
			frappe.delete_doc("CRM Daily Allocation", t_id, force=True, ignore_permissions=True)
			if contact_name and frappe.db.exists("Contact", contact_name):
				from frappe.desk.form import assign_to
				try:
					assign_to.clear("Contact", contact_name, ignore_permissions=True)
				except Exception:
					pass
				frappe.db.set_value("Contact", contact_name, "_assign", None, update_modified=False)
			deleted += 1

	frappe.db.commit()
	try:
		frappe.publish_realtime("crm_tasks_updated", {"deleted": deleted}, after_commit=True)
	except Exception:
		pass

	return {"success": True, "deleted": deleted, "message": _("Deleted {0} task(s).").format(deleted)}


@frappe.whitelist()
def get_task_for_contact(contact: str, task_name: str | None = None) -> dict[str, Any] | None:
	"""Fetch active task details for a given contact and current session user."""
	current_user = frappe.session.user
	is_admin = is_admin_user(current_user)

	if task_name and frappe.db.exists("CRM Daily Allocation", task_name):
		task = frappe.get_doc("CRM Daily Allocation", task_name)
		if is_admin or task.assigned_to == current_user:
			return {
				"name": str(task.name),
				"contact": task.contact,
				"contact_name": task.contact_name or task.contact,
				"organization": task.organization or "",
				"status": task.status or "To Do",
				"assigned_to": task.assigned_to,
				"assigned_to_name": frappe.db.get_value("User", task.assigned_to, "full_name") or task.assigned_to,
				"allocated_by": task.allocated_by,
				"allocated_by_name": frappe.db.get_value("User", task.allocated_by, "full_name") or task.allocated_by,
				"allocation_date": str(task.allocation_date),
				"notes": task.notes or "",
				"follow_up_date": str(task.follow_up_date) if task.follow_up_date else "",
				"country": task.country or "Not Available",
				"timezone": format_timezone_label(task.timezone, task.country),
			}

	filters = {"contact": contact}
	if not is_admin:
		filters["assigned_to"] = current_user

	tasks = frappe.get_all(
		"CRM Daily Allocation",
		filters=filters,
		fields=[
			"name", "contact", "contact_name", "organization", "status",
			"assigned_to", "allocated_by", "allocation_date", "notes", "follow_up_date",
			"country", "timezone",
		],
		order_by="allocation_date desc, creation desc",
		limit=1,
	)
	if tasks:
		t = tasks[0]
		return {
			"name": str(t.name),
			"contact": t.contact,
			"contact_name": t.contact_name or t.contact,
			"organization": t.organization or "",
			"status": t.status or "To Do",
			"assigned_to": t.assigned_to,
			"assigned_to_name": frappe.db.get_value("User", t.assigned_to, "full_name") or t.assigned_to,
			"allocated_by": t.allocated_by,
			"allocated_by_name": frappe.db.get_value("User", t.allocated_by, "full_name") or t.allocated_by,
			"allocation_date": str(t.allocation_date),
			"notes": t.notes or "",
			"follow_up_date": str(t.follow_up_date) if t.follow_up_date else "",
			"country": t.country or "Not Available",
			"timezone": format_timezone_label(t.timezone, t.country),
		}
	return None


@frappe.whitelist()
def get_email_templates(search: str | None = None) -> list[dict[str, Any]]:
	"""Fetch enabled email templates for composer selection."""
	import re
	filters = {"enabled": 1}
	templates = frappe.get_all(
		"Email Template",
		filters=filters,
		fields=["name", "subject", "response", "response_html", "use_html", "modified"],
		order_by="modified desc",
	)

	search_lower = (search or "").strip().lower()
	results = []

	for t in templates:
		subj = t.subject or ""
		body = t.response_html or t.response or ""
		clean_preview = re.sub(r"<[^>]+>", " ", body).strip()
		clean_preview = " ".join(clean_preview.split())[:140]

		if search_lower:
			if (
				search_lower not in t.name.lower()
				and search_lower not in subj.lower()
				and search_lower not in clean_preview.lower()
			):
				continue

		results.append({
			"name": t.name,
			"subject": subj,
			"preview": clean_preview,
			"response": body,
		})

	return results


@frappe.whitelist()
def render_email_template(template_name: str, contact: str | None = None) -> dict[str, Any]:
	"""Render email template with personalization variables for the given contact/prospect."""
	import re
	if not frappe.db.exists("Email Template", template_name):
		frappe.throw(_("Email Template '{0}' not found.").format(template_name), frappe.DoesNotExistError)

	template = frappe.get_doc("Email Template", template_name)
	contact_doc = frappe.get_doc("Contact", contact) if (contact and frappe.db.exists("Contact", contact)) else None

	doc_dict = contact_doc.as_dict() if contact_doc else {}
	first_name = doc_dict.get("first_name") or (doc_dict.get("full_name") or "").split(" ")[0] or ""
	last_name = doc_dict.get("last_name") or ""
	full_name = doc_dict.get("full_name") or f"{first_name} {last_name}".strip() or "there"
	org_name = doc_dict.get("company_name") or ""

	doc_dict["first_name"] = first_name
	doc_dict["last_name"] = last_name
	doc_dict["full_name"] = full_name
	doc_dict["organization"] = org_name
	doc_dict["prospect_name"] = full_name
	doc_dict["company_name"] = org_name

	context = {
		"doc": doc_dict,
		"first_name": first_name,
		"last_name": last_name,
		"full_name": full_name,
		"organization": org_name,
		"company_name": org_name,
		"prospect_name": full_name,
		"email": doc_dict.get("email_id") or "",
		"mobile_no": doc_dict.get("mobile_no") or "",
	}

	try:
		rendered_subject = frappe.render_template(template.subject or "", context)
	except Exception:
		rendered_subject = template.subject or ""

	raw_body = template.response_html or template.response or ""
	try:
		rendered_body = frappe.render_template(raw_body, context)
	except Exception:
		rendered_body = raw_body

	# Clean up any leftover unparsed Jinja markers if any
	rendered_subject = re.sub(r"\{\{[^}]+\}\}", "", rendered_subject).strip()

	return {
		"name": template.name,
		"subject": rendered_subject,
		"content": rendered_body,
	}


@frappe.whitelist()
def send_task_email(
	task_name: str | None = None,
	contact: str | None = None,
	recipient: str | None = None,
	subject: str | None = None,
	content: str | None = None,
	cc: str | None = None,
	bcc: str | None = None,
	attachments: Any = None,
) -> dict[str, Any]:
	"""Send an email from My Task workspace for a specific allocated task."""
	current_user = frappe.session.user
	is_admin = is_admin_user(current_user)

	contact_name = contact
	task_doc = None

	if task_name and frappe.db.exists("CRM Daily Allocation", task_name):
		task_doc = frappe.get_doc("CRM Daily Allocation", task_name)
		if not is_admin and task_doc.assigned_to != current_user:
			frappe.throw(_("Permission denied. You can only send emails for your own tasks."), frappe.PermissionError)
		contact_name = task_doc.contact
	elif contact:
		# Locate active task for current user or admin
		t_filters = {"contact": contact}
		if not is_admin:
			t_filters["assigned_to"] = current_user
		t_name = frappe.db.get_value("CRM Daily Allocation", t_filters, "name")
		if t_name:
			task_doc = frappe.get_doc("CRM Daily Allocation", t_name)
			task_name = task_doc.name
	else:
		frappe.throw(_("Either task_name or contact must be provided."))

	if not recipient and contact_name and frappe.db.exists("Contact", contact_name):
		c_doc = frappe.get_doc("Contact", contact_name)
		recipient = c_doc.email_id or (c_doc.email_ids[0].email_id if c_doc.email_ids else "")

	if not recipient:
		frappe.throw(_("Recipient email is required."))
	if not subject or not content:
		frappe.throw(_("Subject and content are required."))

	user_fullname = frappe.db.get_value("User", current_user, "full_name") or current_user

	comm = frappe.new_doc("Communication")
	comm.communication_type = "Communication"
	comm.communication_medium = "Email"
	comm.sent_or_received = "Sent"
	comm.sender = current_user
	comm.sender_full_name = user_fullname
	comm.recipients = recipient
	comm.cc = cc or ""
	comm.bcc = bcc or ""
	comm.subject = subject
	comm.content = content
	comm.reference_doctype = "Contact"
	comm.reference_name = contact_name
	comm.delivery_status = "Sent"
	comm.flags.ignore_permissions = True
	comm.insert()

	# Process attachments if supplied
	if attachments:
		if isinstance(attachments, str):
			try:
				attachments = json.loads(attachments)
			except Exception:
				attachments = [a.strip() for a in attachments.split(",") if a.strip()]
		if isinstance(attachments, list):
			for att in attachments:
				file_url = att.get("file_url") if isinstance(att, dict) else str(att)
				if file_url:
					file_name = frappe.db.get_value("File", {"file_url": file_url}, "name")
					if file_name:
						frappe.db.set_value("File", file_name, {
							"attached_to_doctype": "Communication",
							"attached_to_name": comm.name,
						})

	# Advance task from To Do to In Progress if currently To Do
	if task_name and frappe.db.get_value("CRM Daily Allocation", task_name, "status") == "To Do":
		frappe.db.set_value("CRM Daily Allocation", task_name, "status", "In Progress")
	elif contact_name:
		check_and_advance_task_to_in_progress(contact=contact_name, email=recipient)

	frappe.db.commit()
	return {"success": True, "communication": comm.name, "task_status": "In Progress"}


@frappe.whitelist()
def log_task_call(
	task_name: str,
	call_type: str = "Outgoing",
	phone: str | None = None,
	duration: int | str = 0,
	status: str = "Completed",
	note: str | None = None,
) -> dict[str, Any]:
	"""Log a phone call from My Task workspace for a specific allocated task."""
	if not frappe.db.exists("CRM Daily Allocation", task_name):
		frappe.throw(_("Task {0} not found.").format(task_name), frappe.DoesNotExistError)

	task = frappe.get_doc("CRM Daily Allocation", task_name)
	current_user = frappe.session.user
	if not is_admin_user(current_user) and task.assigned_to != current_user:
		frappe.throw(_("Permission denied. You can only log calls for your own tasks."), frappe.PermissionError)

	phone_val = phone or task.mobile_no or "0000000000"

	try:
		dur_val = int(duration)
	except (ValueError, TypeError):
		dur_val = 0

	call_doc = frappe.new_doc("CRM Call Log")
	call_doc.type = call_type
	call_doc.status = status
	call_doc.duration = dur_val
	call_doc.reference_doctype = "Contact"
	call_doc.reference_docname = task.contact

	user_phone = frappe.db.get_value("User", current_user, "phone") or "+10000000000"
	if call_type == "Outgoing":
		call_doc.caller = current_user
		call_doc.receiver = None
		call_doc.to = phone_val
		setattr(call_doc, "from", user_phone)
	else:
		call_doc.receiver = current_user
		call_doc.caller = None
		setattr(call_doc, "from", phone_val)
		call_doc.to = user_phone

	call_doc.flags.ignore_permissions = True
	call_doc.insert()

	if note:
		note_doc = frappe.new_doc("FCRM Note")
		note_doc.title = _("Call with {0}").format(task.contact_name or task.contact)
		note_doc.content = note
		note_doc.reference_doctype = "CRM Call Log"
		note_doc.reference_docname = call_doc.name
		note_doc.flags.ignore_permissions = True
		note_doc.insert()
		frappe.db.set_value("CRM Call Log", call_doc.name, "note", note_doc.name)

	# If status == 'Completed' and task is currently 'To Do', advance to 'In Progress'
	if status == "Completed" and frappe.db.get_value("CRM Daily Allocation", task_name, "status") == "To Do":
		frappe.db.set_value("CRM Daily Allocation", task_name, "status", "In Progress")

	frappe.db.commit()
	current_status = frappe.db.get_value("CRM Daily Allocation", task_name, "status")
	return {"success": True, "name": call_doc.name, "task_status": current_status}


@frappe.whitelist()
def bulk_update_tasks(
	tasks: Any,
	status: str | None = None,
	notes: str | None = None,
	follow_up_date: str | None = None,
) -> dict[str, Any]:
	"""Bulk update workflow status, notes, or follow-up date for selected tasks."""
	current_user = frappe.session.user
	is_admin = is_admin_user(current_user)

	if isinstance(tasks, str):
		try:
			tasks = json.loads(tasks)
		except Exception:
			tasks = [t.strip() for t in tasks.split(",") if t.strip()]

	allowed_statuses = set(VALID_STATUSES) | set(LEGACY_STATUSES)
	if status and status not in allowed_statuses:
		frappe.throw(_("Invalid status {0}. Allowed: {1}").format(status, ", ".join(VALID_STATUSES)))

	updated = 0
	for t_id in tasks:
		if frappe.db.exists("CRM Daily Allocation", t_id):
			doc = frappe.get_doc("CRM Daily Allocation", t_id)
			if not is_admin and doc.assigned_to != current_user:
				continue
			if status:
				doc.status = status
			if notes is not None:
				doc.notes = notes
			if follow_up_date is not None:
				doc.follow_up_date = follow_up_date or None
			doc.flags.ignore_permissions = True
			doc.save()
			updated += 1

	frappe.db.commit()
	return {"success": True, "updated": updated, "message": _("Updated {0} task(s).").format(updated)}


@frappe.whitelist()
def send_bulk_email(
	doctype: str,
	names: Any,
	subject: str,
	content: str,
	template_name: str | None = None,
) -> dict[str, Any]:
	"""Send bulk email to selected Contacts, Leads, or Tasks and advance To Do tasks to In Progress."""
	if isinstance(names, str):
		try:
			names = json.loads(names)
		except Exception:
			names = [n.strip() for n in names.split(",") if n.strip()]

	if not names:
		frappe.throw(_("Please select at least one recipient."))

	if not subject or not content:
		frappe.throw(_("Email subject and content cannot be empty."))

	current_user = frappe.session.user
	user_fullname = frappe.db.get_value("User", current_user, "full_name") or current_user

	sent_count = 0
	skipped_count = 0
	errors = []

	for item in names:
		recip_email = ""
		contact_name = None
		lead_name = None

		if doctype == "CRM Lead":
			lead_name = item
			recip_email = frappe.db.get_value("CRM Lead", item, "email") or ""
		elif doctype == "Contact":
			contact_name = item
			c_doc = frappe.get_doc("Contact", item)
			recip_email = c_doc.email_id or (c_doc.email_ids[0].email_id if c_doc.email_ids else "")
			lead_name = resolve_lead_for_contact(item)
		elif doctype == "CRM Daily Allocation":
			t_doc = frappe.db.get_value("CRM Daily Allocation", item, ["contact", "email"], as_dict=True)
			if t_doc:
				contact_name = t_doc.contact
				recip_email = t_doc.email or ""
				lead_name = resolve_lead_for_contact(contact_name)

		if not recip_email:
			skipped_count += 1
			errors.append(f"{item}: No valid email address found")
			continue

		try:
			comm = frappe.new_doc("Communication")
			comm.communication_type = "Communication"
			comm.communication_medium = "Email"
			comm.sent_or_received = "Sent"
			comm.sender = current_user
			comm.sender_full_name = user_fullname
			comm.recipients = recip_email
			comm.subject = subject
			comm.content = content
			comm.reference_doctype = "Contact" if contact_name else ("CRM Lead" if lead_name else "Contact")
			comm.reference_name = contact_name or lead_name or item
			comm.delivery_status = "Sent"
			comm.flags.ignore_permissions = True
			comm.insert()

			# Advance allocated task from To Do to In Progress
			check_and_advance_task_to_in_progress(contact=contact_name, lead=lead_ref if (lead_ref := lead_name) else None, email=recip_email)
			sent_count += 1
		except Exception as e:
			errors.append(f"{item}: {str(e)}")

	frappe.db.commit()

	return {
		"success": True,
		"sent": sent_count,
		"skipped": skipped_count,
		"errors": errors,
		"message": _("Sent bulk email to {0} recipient(s).").format(sent_count),
	}


