from __future__ import annotations

import json
import re
from typing import Any

import frappe
from frappe import _


def validate(doc, method):
	update_deals_email_mobile_no(doc)
	sync_allocation_fields_on_contact_update(doc)


def sync_allocation_fields_on_contact_update(doc):
	name = getattr(doc, "name", None)
	if not name:
		return
	if frappe.db.exists("CRM Daily Allocation", {"contact": name}):
		full_name = doc.full_name or f"{doc.first_name or ''} {doc.last_name or ''}".strip() or name
		c_email = doc.email_id or (doc.email_ids[0].email_id if getattr(doc, "email_ids", None) else "") or ""
		c_phone = doc.mobile_no or (doc.phone_nos[0].phone if getattr(doc, "phone_nos", None) else "") or ""
		org_name = doc.company_name or ""
		from crm.api.daily_allocation import resolve_country_for_contact, get_timezone_for_country
		cntry = resolve_country_for_contact(name, org_name)
		tz = get_timezone_for_country(cntry) if cntry else "Not Available"

		frappe.db.set_value(
			"CRM Daily Allocation",
			{"contact": name},
			{
				"contact_name": full_name,
				"organization": org_name,
				"email": c_email,
				"mobile_no": c_phone,
				"country": cntry or "",
				"timezone": tz if tz != "Not Available" else "",
			},
			update_modified=False,
		)


def update_deals_email_mobile_no(doc):
	linked_deals = frappe.get_all(
		"CRM Contacts",
		filters={"contact": doc.name, "is_primary": 1},
		fields=["parent"],
	)

	for linked_deal in linked_deals:
		deal = frappe.db.get_values("CRM Deal", linked_deal.parent, ["email", "mobile_no"], as_dict=True)[0]
		if deal.email != doc.email_id or deal.mobile_no != doc.mobile_no:
			frappe.db.set_value(
				"CRM Deal",
				linked_deal.parent,
				{
					"email": doc.email_id,
					"mobile_no": doc.mobile_no,
				},
			)


@frappe.whitelist()
def get_linked_deals(contact: str) -> list[dict[str, Any]]:
	"""The deals that list the contact and that the user can read, the last changed first."""
	if not frappe.has_permission("Contact", "read", contact):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	return frappe.get_list(
		"CRM Deal",
		filters=[["CRM Contacts", "contact", "=", contact]],
		fields=[
			"name",
			"organization",
			"organization.organization_logo as organization_logo",
			"currency",
			"deal_value",
			"status",
			"email",
			"mobile_no",
			"deal_owner",
			"deal_owner.full_name as deal_owner_name",
			"modified",
		],
		order_by="modified desc",
		distinct=True,
	)


@frappe.whitelist()
def create_new(contact: str, field: str, value: str) -> bool:
	"""Create new email or phone for a contact"""
	if not frappe.has_permission("Contact", "write", contact):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	contact_doc = frappe.get_cached_doc("Contact", contact)

	if field == "email":
		email = {"email_id": value, "is_primary": 1 if len(contact_doc.email_ids) == 0 else 0}
		contact_doc.append("email_ids", email)
	elif field in ("mobile_no", "phone"):
		mobile_no = {"phone": value, "is_primary_mobile_no": 1 if len(contact_doc.phone_nos) == 0 else 0}
		contact_doc.append("phone_nos", mobile_no)
	else:
		frappe.throw(_("Invalid field"))

	contact_doc.save()
	return True


@frappe.whitelist()
def set_as_primary(contact: str, field: str, value: str) -> bool:
	"""Set email or phone as primary for a contact"""
	if not frappe.has_permission("Contact", "write", contact):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	contact_doc = frappe.get_doc("Contact", contact)

	if field == "email":
		for email in contact_doc.email_ids:
			if email.email_id == value:
				email.is_primary = 1
			else:
				email.is_primary = 0
	elif field in ("mobile_no", "phone"):
		name = "is_primary_mobile_no" if field == "mobile_no" else "is_primary_phone"
		for phone in contact_doc.phone_nos:
			if phone.phone == value:
				phone.set(name, 1)
			else:
				phone.set(name, 0)
	else:
		frappe.throw(_("Invalid field"))

	contact_doc.save()
	return True


@frappe.whitelist()
def search_emails(txt: str | None = None) -> list[Any]:
	doctype = "Contact"
	meta = frappe.get_meta(doctype)
	filters = [["Contact", "email_id", "is", "set"]]

	if meta.get("fields", {"fieldname": "enabled", "fieldtype": "Check"}):
		filters.append([doctype, "enabled", "=", 1])
	if meta.get("fields", {"fieldname": "disabled", "fieldtype": "Check"}):
		filters.append([doctype, "disabled", "!=", 1])

	or_filters = []
	search_fields = ["full_name", "email_id", "name"]
	if txt:
		for f in search_fields:
			or_filters.append([doctype, f.strip(), "like", f"%{txt}%"])

	results = frappe.get_list(
		doctype,
		filters=filters,
		fields=search_fields,
		or_filters=or_filters,
		limit_start=0,
		limit_page_length=20,
		order_by="email_id, full_name, name",
		ignore_permissions=False,
		as_list=True,
		strict=False,
	)

	return results


# -------------------------------------------------------------
# CONTACT ACTIVITY ENDPOINTS
# -------------------------------------------------------------

def _format_seconds(seconds: int | float | None) -> str:
	if not seconds:
		return "00:00"
	s = int(seconds)
	mins = s // 60
	secs = s % 60
	return f"{mins:02d}:{secs:02d}"


@frappe.whitelist()
def get_contact_activities(contact: str) -> dict[str, Any]:
	"""Return categorized activities (All, Emails, Calls, Notes, Meetings) for a Contact."""
	if not frappe.has_permission("Contact", "read", contact):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	if not frappe.db.exists("Contact", contact):
		frappe.throw(_("Contact {0} not found").format(contact), frappe.DoesNotExistError)

	contact_doc = frappe.get_doc("Contact", contact)
	emails = [e.email_id.strip() for e in contact_doc.email_ids if e.email_id]
	phones = [p.phone.strip() for p in contact_doc.phone_nos if p.phone]

	# Find linked CRM Leads (by matching email or direct link)
	leads = []
	if emails:
		leads = frappe.get_all("CRM Lead", filters={"email": ["in", emails]}, pluck="name")

	# Attached call notes to exclude from standalone notes tab
	call_names_pre = set()
	for c in frappe.db.get_all("CRM Call Log", filters={"reference_doctype": "Contact", "reference_docname": contact}, pluck="name"):
		call_names_pre.add(c)
	for c in frappe.db.get_all("Dynamic Link", filters={"link_doctype": "Contact", "link_name": contact, "parenttype": "CRM Call Log"}, pluck="parent"):
		call_names_pre.add(c)
	for l in leads:
		for c in frappe.db.get_all("CRM Call Log", filters={"reference_doctype": "CRM Lead", "reference_docname": l}, pluck="name"):
			call_names_pre.add(c)
	for p in phones:
		for c in frappe.db.sql("SELECT name FROM `tabCRM Call Log` WHERE `from` = %s OR `to` = %s", (p, p), as_dict=True):
			call_names_pre.add(c.name)

	call_attached_notes = set()
	if call_names_pre:
		call_attached_notes = set(
			frappe.db.get_all(
				"CRM Call Log",
				filters={"name": ["in", list(call_names_pre)], "note": ["is", "set"]},
				pluck="note",
			)
		)

	# ---------------------------------------------------------
	# 1. NOTES (FCRM Note)
	# ---------------------------------------------------------
	note_names = set()
	for n in frappe.db.get_all("FCRM Note", filters={"reference_doctype": "Contact", "reference_docname": contact}, pluck="name"):
		note_names.add(n)
	for n in frappe.db.get_all("Dynamic Link", filters={"link_doctype": "Contact", "link_name": contact, "parenttype": "FCRM Note"}, pluck="parent"):
		note_names.add(n)
	for l in leads:
		for n in frappe.db.get_all("FCRM Note", filters={"reference_doctype": "CRM Lead", "reference_docname": l}, pluck="name"):
			note_names.add(n)

	# Exclude notes that are attached to call logs so they only appear inside the Call card
	note_names = note_names - call_attached_notes

	notes_list = []
	if note_names:
		raw_notes = frappe.get_all(
			"FCRM Note",
			filters={"name": ["in", list(note_names)]},
			fields=["name", "title", "content", "pinned", "pinned_by", "pinned_on", "owner", "creation", "modified"],
			order_by="creation desc",
		)
		for n in raw_notes:
			author = frappe.db.get_value("User", n.owner, "full_name") or n.owner or "User"
			notes_list.append({
				"activity_type": "note",
				"name": n.name,
				"title": n.title or _("Note"),
				"content": n.content or "",
				"owner": n.owner,
				"author_name": author,
				"creation": str(n.creation),
				"modified": str(n.modified),
				"date": str(n.creation),
				"pinned": bool(n.pinned),
				"pinned_by": n.pinned_by,
				"pinned_on": str(n.pinned_on) if n.pinned_on else None,
				"activity_title": _("{0} added a note").format(author),
			})

	# ---------------------------------------------------------
	# 2. CALLS (CRM Call Log)
	# ---------------------------------------------------------
	call_names = set(call_names_pre)

	calls_list = []
	if call_names:
		raw_calls = frappe.get_all(
			"CRM Call Log",
			filters={"name": ["in", list(call_names)]},
			fields=[
				"name", "caller", "receiver", "from", "to", "duration",
				"start_time", "end_time", "status", "type", "recording_url",
				"creation", "note", "owner"
			],
			order_by="creation desc",
		)
		for c in raw_calls:
			note_text = ""
			if c.note:
				note_text = frappe.db.get_value("FCRM Note", c.note, "content") or str(c.note)

			dur = c.duration or 0
			call_type = c.type or "Outgoing"
			user_id = c.caller if call_type == "Outgoing" else c.receiver
			user_name = (frappe.db.get_value("User", user_id, "full_name") if user_id else None) or user_id or c.owner or "User"
			phone_no = c.to if call_type == "Outgoing" else getattr(c, "from")

			calls_list.append({
				"activity_type": "call",
				"name": c.name,
				"type": call_type,
				"caller": c.caller,
				"receiver": c.receiver,
				"user": user_id,
				"user_name": user_name,
				"phone": phone_no or (phones[0] if phones else ""),
				"prospect_name": contact_doc.full_name,
				"duration": dur,
				"duration_formatted": _format_seconds(dur),
				"status": c.status or "Completed",
				"start_time": str(c.start_time or c.creation),
				"date": str(c.start_time or c.creation),
				"creation": str(c.creation),
				"note": note_text,
				"recording_url": c.recording_url or "",
				"activity_title": _("{0} had a call with this prospect").format(user_name),
			})

	# ---------------------------------------------------------
	# 3. MEETINGS (Event)
	# ---------------------------------------------------------
	event_names = set()
	for e in frappe.db.get_all("Event", filters={"reference_doctype": "Contact", "reference_docname": contact}, pluck="name"):
		event_names.add(e)
	for e in frappe.db.get_all("Event Participants", filters={"reference_doctype": "Contact", "reference_docname": contact}, pluck="parent"):
		event_names.add(e)
	for email in emails:
		for e in frappe.db.get_all("Event Participants", filters={"email": email}, pluck="parent"):
			event_names.add(e)
	for e in frappe.db.get_all("Dynamic Link", filters={"link_doctype": "Contact", "link_name": contact, "parenttype": "Event"}, pluck="parent"):
		event_names.add(e)
	for l in leads:
		for e in frappe.db.get_all("Event", filters={"reference_doctype": "CRM Lead", "reference_docname": l}, pluck="name"):
			event_names.add(e)
		for e in frappe.db.get_all("Event Participants", filters={"reference_doctype": "CRM Lead", "reference_docname": l}, pluck="parent"):
			event_names.add(e)

	meetings_list = []
	if event_names:
		raw_events = frappe.get_all(
			"Event",
			filters={"name": ["in", list(event_names)]},
			fields=["name", "subject", "starts_on", "ends_on", "owner", "status", "description", "creation"],
			order_by="starts_on desc",
		)
		for e in raw_events:
			organizer = frappe.db.get_value("User", e.owner, "full_name") or e.owner or "User"
			parts = frappe.get_all("Event Participants", filters={"parent": e.name}, fields=["reference_doctype", "reference_docname", "email"])
			part_labels = []
			for p in parts:
				lbl = p.email or p.reference_docname
				if lbl and lbl not in part_labels:
					part_labels.append(lbl)

			meetings_list.append({
				"activity_type": "meeting",
				"name": e.name,
				"title": e.subject or _("Meeting"),
				"starts_on": str(e.starts_on),
				"ends_on": str(e.ends_on),
				"date": str(e.starts_on or e.creation),
				"creation": str(e.creation),
				"owner": e.owner,
				"organizer_name": organizer,
				"status": e.status or "Open",
				"description": e.description or "",
				"participants": part_labels or ([contact_doc.full_name] if contact_doc.full_name else []),
				"activity_title": _("Meeting scheduled"),
			})

	# ---------------------------------------------------------
	# 4. EMAILS (Communication)
	# ---------------------------------------------------------
	comm_names = set()
	for c in frappe.db.get_all(
		"Communication",
		filters={
			"reference_doctype": "Contact",
			"reference_name": contact,
			"communication_medium": ["in", ["Email", ""]],
			"communication_type": ["in", ["Communication", "Automated Message"]],
		},
		pluck="name",
	):
		comm_names.add(c)
	for c in frappe.db.get_all("Communication Link", filters={"link_doctype": "Contact", "link_name": contact}, pluck="parent"):
		comm_names.add(c)
	for l in leads:
		for c in frappe.db.get_all(
			"Communication",
			filters={
				"reference_doctype": "CRM Lead",
				"reference_name": l,
				"communication_medium": ["in", ["Email", ""]],
				"communication_type": ["in", ["Communication", "Automated Message"]],
			},
			pluck="name",
		):
			comm_names.add(c)
		for c in frappe.db.get_all("Communication Link", filters={"link_doctype": "CRM Lead", "link_name": l}, pluck="parent"):
			comm_names.add(c)
	for email in emails:
		for c in frappe.db.sql(
			"SELECT name FROM `tabCommunication` WHERE (sender = %s OR recipients LIKE %s) AND communication_type IN ('Communication', 'Automated Message') AND (communication_medium = 'Email' OR communication_medium IS NULL OR communication_medium = '')",
			(email, f"%{email}%"),
			as_dict=True,
		):
			comm_names.add(c.name)

	emails_list = []
	if comm_names:
		raw_comms = frappe.get_all(
			"Communication",
			filters={
				"name": ["in", list(comm_names)],
				"communication_medium": ["in", ["Email", ""]],
				"communication_type": ["in", ["Communication", "Automated Message"]],
			},
			fields=[
				"name", "sender", "sender_full_name", "recipients", "cc", "bcc",
				"subject", "content", "communication_date", "creation", "delivery_status"
			],
			order_by="creation desc",
		)
		for c in raw_comms:
			attached_files = frappe.get_all(
				"File",
				filters={"attached_to_doctype": "Communication", "attached_to_name": c.name},
				fields=["name", "file_name", "file_url", "file_size"],
			)
			raw_html = c.content or ""
			clean_text = re.sub(r"<[^>]+>", " ", raw_html).strip()
			clean_text = " ".join(clean_text.split())
			snippet = clean_text[:140] + ("..." if len(clean_text) > 140 else "")

			sender_display = c.sender_full_name or c.sender or "User"
			emails_list.append({
				"activity_type": "email",
				"name": c.name,
				"sender": c.sender or "",
				"sender_full_name": sender_display,
				"recipients": c.recipients or "",
				"cc": c.cc or "",
				"bcc": c.bcc or "",
				"subject": c.subject or _("(No Subject)"),
				"content": raw_html,
				"snippet": snippet,
				"date": str(c.communication_date or c.creation),
				"creation": str(c.creation),
				"delivery_status": c.delivery_status or "Sending",
				"attachments": attached_files,
				"activity_title": _("{0} sent an email to this prospect").format(sender_display),
			})

	# ---------------------------------------------------------
	# COMBINE ALL CHRONOLOGICALLY (NEWEST FIRST)
	# ---------------------------------------------------------
	all_activities = sorted(
		notes_list + calls_list + meetings_list + emails_list,
		key=lambda x: str(x.get("date") or x.get("creation") or ""),
		reverse=True,
	)

	return {
		"all_activities": all_activities,
		"emails": emails_list,
		"calls": calls_list,
		"notes": notes_list,
		"meetings": meetings_list,
		"counts": {
			"all_activity": len(all_activities),
			"emails": len(emails_list),
			"calls": len(calls_list),
			"notes": len(notes_list),
			"meetings": len(meetings_list),
		},
	}


@frappe.whitelist()
def add_contact_note(contact: str, title: str | None = None, content: str | None = None, pinned: int | bool = 0) -> dict[str, Any]:
	"""Create a new Note linked to a Contact."""
	if not frappe.has_permission("Contact", "write", contact):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	if not content and not title:
		frappe.throw(_("Note title or content is required."))

	note_doc = frappe.new_doc("FCRM Note")
	note_doc.title = title or _("Note")
	note_doc.content = content or ""
	note_doc.reference_doctype = "Contact"
	note_doc.reference_docname = contact
	note_doc.pinned = 1 if pinned else 0
	note_doc.flags.ignore_permissions = True
	note_doc.insert()
	frappe.db.commit()

	return {"success": True, "name": note_doc.name}


@frappe.whitelist()
def log_contact_call(
	contact: str,
	call_type: str = "Outgoing",
	phone: str | None = None,
	duration: int | str = 0,
	status: str = "Completed",
	note: str | None = None,
	start_time: str | None = None,
) -> dict[str, Any]:
	"""Log a Call associated with a Contact."""
	if not frappe.has_permission("Contact", "write", contact):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	contact_doc = frappe.get_doc("Contact", contact)
	phone_val = phone or (contact_doc.phone_nos[0].phone if contact_doc.phone_nos else "") or "0000000000"

	try:
		dur_val = int(duration)
	except (ValueError, TypeError):
		dur_val = 0

	call_doc = frappe.new_doc("CRM Call Log")
	call_doc.type = call_type
	call_doc.status = status
	call_doc.duration = dur_val
	call_doc.reference_doctype = "Contact"
	call_doc.reference_docname = contact

	current_user = frappe.session.user
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

	if start_time:
		call_doc.start_time = start_time

	call_doc.flags.ignore_permissions = True
	call_doc.insert()

	if note:
		note_doc = frappe.new_doc("FCRM Note")
		note_doc.title = _("Call with {0}").format(contact_doc.full_name)
		note_doc.content = note
		note_doc.reference_doctype = "CRM Call Log"
		note_doc.reference_docname = call_doc.name
		note_doc.flags.ignore_permissions = True
		note_doc.insert()
		frappe.db.set_value("CRM Call Log", call_doc.name, "note", note_doc.name)

	frappe.db.commit()

	if status == "Completed":
		try:
			from crm.api.daily_allocation import check_and_advance_task_to_in_progress
			check_and_advance_task_to_in_progress(contact=contact, phone=phone_val)
		except Exception as e:
			frappe.logger().error(f"Error advancing task status: {e}")

	return {"success": True, "name": call_doc.name}


@frappe.whitelist()
def schedule_contact_meeting(
	contact: str,
	title: str,
	starts_on: str,
	ends_on: str,
	description: str | None = None,
	status: str = "Open",
	location: str | None = None,
	participants: Any = None,
) -> dict[str, Any]:
	"""Schedule a Meeting (Event) associated with a Contact."""
	if not frappe.has_permission("Contact", "write", contact):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	contact_doc = frappe.get_doc("Contact", contact)
	contact_email = contact_doc.email_id or (contact_doc.email_ids[0].email_id if contact_doc.email_ids else "")

	event = frappe.new_doc("Event")
	event.subject = title
	event.event_category = "Meeting"
	event.event_type = "Public"
	event.starts_on = starts_on
	event.ends_on = ends_on
	event.status = status
	event.description = description or ""
	event.reference_doctype = "Contact"
	event.reference_docname = contact

	event.append("event_participants", {
		"reference_doctype": "Contact",
		"reference_docname": contact,
		"email": contact_email,
	})

	if participants:
		part_list = participants if isinstance(participants, list) else [p.strip() for p in str(participants).split(",") if p.strip()]
		for p in part_list:
			if p != contact_email:
				event.append("event_participants", {"email": p})

	event.flags.ignore_permissions = True
	event.insert()
	frappe.db.commit()

	return {"success": True, "name": event.name}


@frappe.whitelist()
def send_contact_email(
	contact: str,
	recipient: str,
	subject: str,
	content: str,
	cc: str | None = None,
	bcc: str | None = None,
) -> dict[str, Any]:
	"""Disallow direct email sending from Contact detail page."""
	frappe.throw(
		_("Email composition from Contact detail page is disabled. Please send emails from My Tasks workspace."),
		frappe.PermissionError,
	)


def ensure_contact_custom_fields():
	"""Ensure custom_is_dropped column exists in tabContact."""
	try:
		if not frappe.db.has_column("Contact", "custom_is_dropped"):
			from crm.install import add_contact_custom_fields
			add_contact_custom_fields()
	except Exception:
		pass


@frappe.whitelist()
def get_contact_tab_counts() -> dict[str, Any]:
	"""Dynamic counts for Unassigned, Assigned, Dropped contact tabs."""
	ensure_contact_custom_fields()
	user = frappe.session.user
	from crm.api.security import is_admin_only, get_contact_permission_conditions
	is_admin = is_admin_only(user)

	if is_admin:
		unassigned_count = frappe.db.sql("""
			SELECT COUNT(*) FROM `tabContact`
			WHERE (custom_is_dropped = 0 OR custom_is_dropped IS NULL)
			  AND (_assign IS NULL OR _assign = '' OR _assign = '[]')
		""")[0][0]

		assigned_count = frappe.db.sql("""
			SELECT COUNT(*) FROM `tabContact`
			WHERE (custom_is_dropped = 0 OR custom_is_dropped IS NULL)
			  AND (_assign IS NOT NULL AND _assign != '' AND _assign != '[]')
		""")[0][0]

		dropped_count = frappe.db.sql("""
			SELECT COUNT(*) FROM `tabContact`
			WHERE custom_is_dropped = 1
		""")[0][0]
	else:
		cond = get_contact_permission_conditions(user)
		base_where = f"AND ({cond})" if cond else ""

		unassigned_count = frappe.db.sql(f"""
			SELECT COUNT(*) FROM `tabContact`
			WHERE (custom_is_dropped = 0 OR custom_is_dropped IS NULL)
			  AND (_assign IS NULL OR _assign = '' OR _assign = '[]')
			  {base_where}
		""")[0][0]

		assigned_count = frappe.db.sql(f"""
			SELECT COUNT(*) FROM `tabContact`
			WHERE (custom_is_dropped = 0 OR custom_is_dropped IS NULL)
			  AND (_assign IS NOT NULL AND _assign != '' AND _assign != '[]')
			  {base_where}
		""")[0][0]

		dropped_count = frappe.db.sql(f"""
			SELECT COUNT(*) FROM `tabContact`
			WHERE custom_is_dropped = 1
			  {base_where}
		""")[0][0]

	return {
		"unassigned": unassigned_count,
		"assigned": assigned_count,
		"dropped": dropped_count,
		"is_admin": is_admin,
	}


@frappe.whitelist()
def mark_contacts_dropped(names: Any, dropped: int = 1) -> dict[str, Any]:
	"""Mark selected contacts as Dropped (dropped=1) or Restore them to Unassigned (dropped=0)."""
	from crm.api.security import is_admin_or_manager
	if not is_admin_or_manager():
		frappe.throw(_("Permission denied. Only Administrator or Manager can mark contacts as dropped."), frappe.PermissionError)

	if isinstance(names, str):
		try:
			names = json.loads(names)
		except Exception:
			names = [n.strip() for n in names.split(",") if n.strip()]

	if not names:
		frappe.throw(_("Please select at least one contact."))

	dropped_val = 1 if int(dropped) else 0

	for name in names:
		if frappe.db.exists("Contact", name):
			frappe.db.set_value("Contact", name, "custom_is_dropped", dropped_val)
			if dropped_val == 1:
				frappe.db.delete("CRM Daily Allocation", {"contact": name})
			elif dropped_val == 0:
				# Restoring to Unassigned: clear any assignments
				try:
					from frappe.desk.form import assign_to
					assign_to.clear("Contact", name, ignore_permissions=True)
				except Exception:
					pass

	frappe.db.commit()
	try:
		frappe.publish_realtime("crm_tasks_updated", {"dropped": dropped_val}, after_commit=True)
	except Exception:
		pass
	msg = (
		_("{0} contact(s) marked as Dropped.").format(len(names))
		if dropped_val
		else _("{0} contact(s) restored to Unassigned.").format(len(names))
	)
	return {"success": True, "count": len(names), "message": msg}
