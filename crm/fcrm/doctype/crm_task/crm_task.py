# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.desk.doctype.notification_log.notification_log import enqueue_create_notification
from frappe.desk.form.assign_to import add as assign
from frappe.desk.form.assign_to import notify_assignment
from frappe.desk.form.assign_to import remove as unassign
from frappe.model.document import Document
from frappe.utils import now_datetime


class CRMTask(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from crm.fcrm.doctype.crm_task_item.crm_task_item import CRMTaskItem
		from frappe.types import DF

		assigned_role: DF.Link | None
		assigned_to: DF.Link | None
		assignment_type: DF.Literal["User", "Role"]
		checklist: DF.Table[CRMTaskItem]
		completed_items: DF.Int
		description: DF.TextEditor | None
		due_date: DF.Datetime | None
		name: DF.Int | None
		priority: DF.Literal["Low", "Medium", "High"]
		progress: DF.Percent
		reference_docname: DF.DynamicLink | None
		reference_doctype: DF.Link | None
		start_date: DF.Date | None
		status: DF.Literal["Backlog", "Todo", "In Progress", "Done", "Canceled"]
		title: DF.Data
		total_items: DF.Int
	# end: auto-generated types

	def after_insert(self):
		self.sync_assignment()

	def validate(self):
		old_doc = self.get_doc_before_save()
		self.prevent_unauthorized_reassignment(old_doc)
		self.validate_assignment()
		self.update_checklist_progress(old_doc)

		if not old_doc:
			return

		if old_doc.assigned_to != self.assigned_to:
			self.unassign_from_previous_user(old_doc.assigned_to)
			if self.assigned_to:
				self.assign_to()

	def on_update(self):
		old_doc = self.get_doc_before_save()
		if not old_doc:
			return

		role_changed = (
			self.assignment_type == "Role"
			and (
				old_doc.assignment_type != self.assignment_type
				or old_doc.assigned_role != self.assigned_role
			)
		)
		if role_changed:
			self.notify_role_members()

		progress_changed = old_doc.progress != self.progress or old_doc.status != self.status
		if progress_changed:
			self.notify_creator_of_progress()

	def validate_assignment(self):
		self.assignment_type = self.assignment_type or ("Role" if self.assigned_role else "User")

		if self.assignment_type == "Role":
			if not self.assigned_role:
				frappe.throw(_("Assigned Role is required for role-based tasks"))
			if self.assigned_role in {"All", "Guest"}:
				frappe.throw(_("Tasks cannot be assigned to the {0} role").format(self.assigned_role))
			self.assigned_to = None
		else:
			self.assignment_type = "User"
			self.assigned_role = None

	def prevent_unauthorized_reassignment(self, old_doc):
		if not old_doc or self.owner == frappe.session.user or _is_privileged_user(frappe.session.user):
			return
		if (
			old_doc.assignment_type != self.assignment_type
			or old_doc.assigned_to != self.assigned_to
			or old_doc.assigned_role != self.assigned_role
		):
			frappe.throw(_("Only the task creator can change its assignment"), frappe.PermissionError)

	def update_checklist_progress(self, old_doc=None):
		old_items = {row.name: row for row in (old_doc.checklist or [])} if old_doc else {}

		for row in self.checklist or []:
			old_row = old_items.get(row.name)
			old_status = old_row.status if old_row else None
			if row.status == "Completed":
				if old_status == "Completed" and old_row.completed_by:
					row.completed_by = old_row.completed_by
					row.completed_on = old_row.completed_on
				else:
					row.completed_by = frappe.session.user
					row.completed_on = now_datetime()
			else:
				row.completed_by = None
				row.completed_on = None

		self.total_items = len(self.checklist or [])
		self.completed_items = sum(1 for row in (self.checklist or []) if row.status == "Completed")
		self.progress = round((self.completed_items / self.total_items) * 100, 2) if self.total_items else 0

		if not self.total_items or self.status == "Canceled":
			return
		if self.completed_items == self.total_items:
			self.status = "Done"
		elif self.status == "Done":
			self.status = "In Progress"

	def unassign_from_previous_user(self, user: str | None):
		if user:
			unassign(self.doctype, self.name, user)

	def assign_to(self):
		if self.assigned_to:
			assign(
				{
					"assign_to": [self.assigned_to],
					"doctype": self.doctype,
					"name": self.name,
					"description": self.title or self.description,
				}
			)

	def sync_assignment(self):
		if self.assignment_type == "Role":
			self.notify_role_members()
		else:
			self.assign_to()

	def notify_role_members(self):
		if not self.assigned_role:
			return

		users = frappe.get_all(
			"Has Role",
			filters={"role": self.assigned_role, "parenttype": "User"},
			pluck="parent",
		)
		if not users:
			return
		enabled_users = set(
			frappe.get_all("User", filters={"name": ["in", users], "enabled": 1}, pluck="name")
		)
		for user in enabled_users:
			notify_assignment(
				frappe.session.user,
				user,
				self.doctype,
				self.name,
				action="ASSIGN",
				description=self.title or self.description,
			)

	def notify_creator_of_progress(self):
		if not self.owner or self.owner == frappe.session.user:
			return

		subject = _("{0} updated task {1}").format(
			frappe.bold(frappe.get_cached_value("User", frappe.session.user, "full_name") or frappe.session.user),
			frappe.bold(self.title or self.name),
		)
		enqueue_create_notification(
			self.owner,
			{
				"type": "Alert",
				"document_type": self.doctype,
				"document_name": self.name,
				"subject": subject,
				"from_user": frappe.session.user,
			},
		)

	@staticmethod
	def default_list_data():
		columns = [
			{
				"label": "Title",
				"type": "Data",
				"key": "title",
				"width": "16rem",
			},
			{
				"label": "Status",
				"type": "Select",
				"key": "status",
				"width": "8rem",
			},
			{
				"label": "Priority",
				"type": "Select",
				"key": "priority",
				"width": "8rem",
			},
			{
				"label": "Due Date",
				"type": "Date",
				"key": "due_date",
				"width": "8rem",
			},
			{
				"label": "Assigned To",
				"type": "Link",
				"key": "assigned_to",
				"width": "10rem",
			},
			{
				"label": "Assigned Role",
				"type": "Link",
				"key": "assigned_role",
				"width": "10rem",
			},
			{
				"label": "Progress",
				"type": "Percent",
				"key": "progress",
				"width": "8rem",
			},
			{
				"label": "Last Modified",
				"type": "Datetime",
				"key": "modified",
				"width": "8rem",
			},
		]

		rows = [
			"name",
			"title",
			"description",
			"assigned_to",
			"assignment_type",
			"assigned_role",
			"completed_items",
			"total_items",
			"progress",
			"due_date",
			"status",
			"priority",
			"reference_doctype",
			"reference_docname",
			"modified",
		]
		return {"columns": columns, "rows": rows}

	@staticmethod
	def default_kanban_settings():
		return {
			"column_field": "status",
			"title_field": "title",
			"kanban_fields": '["description", "priority", "creation"]',
		}


def get_permission_query_conditions(user=None):
	user = user or frappe.session.user
	if _is_privileged_user(user):
		return ""

	Task = frappe.qb.DocType("CRM Task")
	condition = (Task.owner == user) | (Task.assigned_to == user)
	roles = frappe.get_roles(user)
	if roles:
		condition |= Task.assigned_role.isin(roles)
	return condition.get_sql(with_namespace=True, quote_char="`", secondary_quote_char="'")


def has_permission(doc, ptype, user):
	user = user or frappe.session.user
	if _is_privileged_user(user):
		return True
	if ptype == "create" or not doc.name:
		return True
	if ptype in {"delete", "cancel"}:
		return doc.owner == user
	return bool(
		doc.owner == user
		or doc.assigned_to == user
		or (doc.assigned_role and doc.assigned_role in frappe.get_roles(user))
	)


def _is_privileged_user(user):
	return user == "Administrator" or "System Manager" in frappe.get_roles(user)
