from __future__ import annotations

from typing import Any

import frappe
from frappe import _


def is_admin_or_manager(user: str | None = None) -> bool:
	"""Return True if user is Administrator or has System Manager / Sales Manager roles."""
	if not user:
		user = frappe.session.user
	if user == "Administrator":
		return True
	user_roles = set(frappe.get_roles(user))
	return bool(user_roles.intersection({"System Manager", "Sales Manager", "Sales Master Manager"}))


def is_admin_only(user: str | None = None) -> bool:
	"""Return True if user is Administrator or System Manager."""
	if not user:
		user = frappe.session.user
	if user == "Administrator":
		return True
	user_roles = set(frappe.get_roles(user))
	return "System Manager" in user_roles


# ------------------------------------------------------------------------------
# 1. DELETE GUARDS
# ------------------------------------------------------------------------------

def guard_contact_delete(doc, method=None):
	"""Only Administrator or System Manager can delete Contacts."""
	if not is_admin_only():
		frappe.throw(_("Permission denied. Only Administrator can delete Contacts."), frappe.PermissionError)


def guard_organization_delete(doc, method=None):
	"""Only Administrator or System Manager can delete CRM Organizations."""
	if not is_admin_only():
		frappe.throw(_("Permission denied. Only Administrator can delete Organizations."), frappe.PermissionError)


def guard_lead_delete(doc, method=None):
	"""Only Administrator or System Manager can delete CRM Leads."""
	if not is_admin_only():
		frappe.throw(_("Permission denied. Only Administrator can delete Leads."), frappe.PermissionError)


def guard_communication_delete(doc, method=None):
	"""Standard users cannot delete email records."""
	if not is_admin_only():
		frappe.throw(_("Permission denied. Sent and received emails cannot be deleted by standard users."), frappe.PermissionError)


def guard_call_log_delete(doc, method=None):
	"""Standard users cannot delete call logs."""
	if not is_admin_only():
		frappe.throw(_("Permission denied. Call logs cannot be deleted by standard users."), frappe.PermissionError)


def guard_note_delete(doc, method=None):
	"""Standard users cannot delete notes."""
	if not is_admin_only():
		frappe.throw(_("Permission denied. Notes cannot be deleted by standard users."), frappe.PermissionError)


def guard_allocation_delete(doc, method=None):
	"""Only Administrator / Manager can delete allocations."""
	if not is_admin_or_manager():
		frappe.throw(_("Permission denied. Only Administrator can delete task allocations."), frappe.PermissionError)


def organization_on_trash(doc, method=None):
	"""Clean up all dependent/linked records before CRM Organization is deleted."""
	name = getattr(doc, "name", None) or str(doc)
	if not name:
		return

	# 1. Clean up Dynamic Link pointing to this organization
	frappe.db.delete("Dynamic Link", {"link_doctype": "CRM Organization", "link_name": name})

	# 2. Clear organization on CRM Deals
	frappe.db.set_value("CRM Deal", {"organization": name}, "organization", None)

	# 3. Clear company_name on Contacts
	frappe.db.set_value("Contact", {"company_name": name}, "company_name", None)
	org_name_val = getattr(doc, "organization_name", None)
	if org_name_val:
		frappe.db.set_value("Contact", {"company_name": org_name_val}, "company_name", None)


# ------------------------------------------------------------------------------
# 2. UPDATE GUARDS (STRICT OUTREACH ACTIVITY PROTECTION)
# ------------------------------------------------------------------------------

def guard_communication_update(doc, method=None):
	"""Emails are strictly read-only after creation for standard users."""
	if getattr(doc, "__islocal", False) or getattr(doc, "is_new", lambda: False)():
		return
	if not is_admin_only():
		frappe.throw(_("Permission denied. Sent emails are read-only and cannot be modified."), frappe.PermissionError)


def guard_call_log_update(doc, method=None):
	"""Call logs are strictly read-only after creation for standard users."""
	if getattr(doc, "__islocal", False) or getattr(doc, "is_new", lambda: False)():
		return
	if not is_admin_only():
		frappe.throw(_("Permission denied. Call logs are read-only and cannot be modified."), frappe.PermissionError)


def guard_note_update(doc, method=None):
	"""Notes are strictly read-only after creation for standard users."""
	if getattr(doc, "__islocal", False) or getattr(doc, "is_new", lambda: False)():
		return
	if not is_admin_only():
		frappe.throw(_("Permission denied. Notes are read-only and cannot be modified."), frappe.PermissionError)


def guard_allocation_update(doc, method=None):
	"""Standard users can ONLY update status and notes of their OWN tasks."""
	if getattr(doc, "__islocal", False) or getattr(doc, "is_new", lambda: False)():
		return

	current_user = frappe.session.user
	if is_admin_or_manager(current_user):
		return

	# Standard user check
	if doc.assigned_to != current_user:
		frappe.throw(_("Permission denied. You can only update your own assigned tasks."), frappe.PermissionError)

	old_doc = doc.get_doc_before_save()
	if old_doc:
		if str(old_doc.assigned_to) != str(doc.assigned_to):
			frappe.throw(_("Permission denied. Standard users cannot reassign tasks."), frappe.PermissionError)
		if str(old_doc.allocation_date) != str(doc.allocation_date):
			frappe.throw(_("Permission denied. Standard users cannot change allocation dates."), frappe.PermissionError)


# ------------------------------------------------------------------------------
# 3. ROLE-BASED DATA VISIBILITY (PERMISSION QUERY CONDITIONS & HOOKS)
# ------------------------------------------------------------------------------

def get_contact_permission_conditions(user: str | None = None) -> str:
	"""Return SQL WHERE condition for Contact list queries.
	
	Administrator and System Managers see all contacts.
	Standard users see only contacts they created/own, contacts assigned to them,
	or contacts allocated to them via Daily Allocation or ToDo.
	"""
	if not user:
		user = frappe.session.user

	if user == "Administrator" or is_admin_only(user):
		return ""

	user_esc = frappe.db.escape(user)
	user_like = frappe.db.escape(f"%{user}%")

	return f"""(
		`tabContact`.owner = {user_esc}
		OR `tabContact`._assign LIKE {user_like}
		OR `tabContact`.name IN (
			SELECT contact FROM `tabCRM Daily Allocation`
			WHERE assigned_to = {user_esc}
		)
		OR `tabContact`.name IN (
			SELECT reference_name FROM `tabToDo`
			WHERE reference_type = 'Contact'
			  AND status != 'Cancelled'
			  AND allocated_to = {user_esc}
		)
	)"""


def has_contact_permission(doc=None, ptype="read", user: str | None = None) -> bool | None:
	"""Validate if user has permission on a Contact record."""
	if not user:
		user = frappe.session.user

	if user == "Administrator" or is_admin_only(user):
		return True

	if doc is None or ptype == "create":
		return True

	if isinstance(doc, str):
		doc_name = doc
		doc_owner = frappe.db.get_value("Contact", doc_name, "owner")
		doc_assign = frappe.db.get_value("Contact", doc_name, "_assign")
	else:
		doc_name = getattr(doc, "name", None)
		if not doc_name:
			return True
		doc_owner = getattr(doc, "owner", None)
		doc_assign = doc.get("_assign") if hasattr(doc, "get") else getattr(doc, "_assign", None)

	if doc_owner == user:
		return True

	if doc_assign and user in doc_assign:
		return True

	if frappe.db.exists("CRM Daily Allocation", {"contact": doc_name, "assigned_to": user}):
		return True

	if frappe.db.exists("ToDo", {"reference_type": "Contact", "reference_name": doc_name, "allocated_to": user, "status": ("!=", "Cancelled")}):
		return True

	return False


def get_organization_permission_conditions(user: str | None = None) -> str:
	"""Return SQL WHERE condition for CRM Organization list queries.
	
	Administrator sees all organizations.
	Standard users see organizations they own or organizations that have
	at least one contact owned by or assigned to the user.
	"""
	if not user:
		user = frappe.session.user

	if user == "Administrator" or is_admin_only(user):
		return ""

	user_esc = frappe.db.escape(user)
	user_like = frappe.db.escape(f"%{user}%")

	return f"""(
		`tabCRM Organization`.owner = {user_esc}
		OR `tabCRM Organization`.name IN (
			SELECT dl.link_name FROM `tabDynamic Link` dl
			JOIN `tabContact` c ON c.name = dl.parent
			WHERE dl.link_doctype = 'CRM Organization'
			  AND dl.parenttype = 'Contact'
			  AND (
				c.owner = {user_esc}
				OR c._assign LIKE {user_like}
				OR c.name IN (SELECT contact FROM `tabCRM Daily Allocation` WHERE assigned_to = {user_esc})
				OR c.name IN (SELECT reference_name FROM `tabToDo` WHERE reference_type = 'Contact' AND status != 'Cancelled' AND allocated_to = {user_esc})
			  )
		)
		OR `tabCRM Organization`.organization_name IN (
			SELECT company_name FROM `tabContact`
			WHERE (
				owner = {user_esc}
				OR _assign LIKE {user_like}
				OR name IN (SELECT contact FROM `tabCRM Daily Allocation` WHERE assigned_to = {user_esc})
				OR name IN (SELECT reference_name FROM `tabToDo` WHERE reference_type = 'Contact' AND status != 'Cancelled' AND allocated_to = {user_esc})
			)
		)
		OR `tabCRM Organization`.name IN (
			SELECT company_name FROM `tabContact`
			WHERE (
				owner = {user_esc}
				OR _assign LIKE {user_like}
				OR name IN (SELECT contact FROM `tabCRM Daily Allocation` WHERE assigned_to = {user_esc})
				OR name IN (SELECT reference_name FROM `tabToDo` WHERE reference_type = 'Contact' AND status != 'Cancelled' AND allocated_to = {user_esc})
			)
		)
	)"""


def has_organization_permission(doc=None, ptype="read", user: str | None = None) -> bool | None:
	"""Validate if user has permission on a CRM Organization record."""
	if not user:
		user = frappe.session.user

	if user == "Administrator" or is_admin_only(user):
		return True

	if doc is None or ptype == "create":
		return True

	if isinstance(doc, str):
		doc_name = doc
		doc_owner = frappe.db.get_value("CRM Organization", doc_name, "owner")
		org_name_val = frappe.db.get_value("CRM Organization", doc_name, "organization_name") or doc_name
	else:
		doc_name = getattr(doc, "name", None)
		if not doc_name:
			return True
		doc_owner = getattr(doc, "owner", None)
		org_name_val = getattr(doc, "organization_name", None) or doc_name

	if doc_owner == user:
		return True

	contact_names_dl = frappe.db.sql("""
		SELECT parent FROM `tabDynamic Link`
		WHERE link_doctype = 'CRM Organization'
		  AND link_name = %s
		  AND parenttype = 'Contact'
	""", (doc_name,), pluck=True)

	contact_names_cn = frappe.db.sql("""
		SELECT name FROM `tabContact`
		WHERE company_name = %s OR company_name = %s
	""", (org_name_val, doc_name), pluck=True)

	all_contact_names = list(set(contact_names_dl + contact_names_cn))
	if not all_contact_names:
		return False

	user_esc = frappe.db.escape(user)
	user_like = frappe.db.escape(f"%{user}%")
	has_linked = frappe.db.sql(f"""
		SELECT name FROM `tabContact`
		WHERE name IN %(contacts)s
		  AND (
			owner = {user_esc}
			OR _assign LIKE {user_like}
			OR name IN (SELECT contact FROM `tabCRM Daily Allocation` WHERE assigned_to = {user_esc})
			OR name IN (SELECT reference_name FROM `tabToDo` WHERE reference_type = 'Contact' AND status != 'Cancelled' AND allocated_to = {user_esc})
		  )
		LIMIT 1
	""", {"contacts": tuple(all_contact_names)})

	return bool(has_linked)
