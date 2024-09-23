# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.desk.form.assign_to import add as assign
from crm.fcrm.doctype.crm_notification.crm_notification import notify_user


class CRMTask(Document):
	def after_insert(self):
		self.assign_to()

	def assign_to(self):
		if self.assigned_to:
			assign({
				"assign_to": [self.assigned_to],
				"doctype": self.doctype,
				"name": self.name,
				"description": self.title or self.description,
			})
			self.notify_assigned_user()

	def notify_assigned_user(self):
		"""
		Notify the assigned user about the task assignment
		"""

		owner = frappe.get_cached_value("User", self.owner, "full_name")
		notification_text = f"""
			<div class="mb-2 leading-5 text-gray-600">
				<span class="font-medium text-gray-900">{ owner }</span>
				<span>{ _('assigned a new task {0} to you').format(
					f'<span class="font-medium text-gray-900">{ self.title }</span>'
				) }</span>
			</div>
		"""

		notify_user({
			"owner": self.owner,
			"assigned_to": self.assigned_to,
			"notification_type": "Task",
			"message": self.description,
			"notification_text": notification_text,
			"doctype": self.doctype,
			"name": self.name,
			"reference_doctype": self.reference_doctype,
			"reference_docname": self.reference_docname,
		})


	@staticmethod
	def default_list_data():
		columns = [
			{
				'label': 'Title',
				'type': 'Data',
				'key': 'title',
				'width': '16rem',
			},
			{
				'label': 'Status',
				'type': 'Select',
				'key': 'status',
				'width': '8rem',
			},
			{
				'label': 'Priority',
				'type': 'Select',
				'key': 'priority',
				'width': '8rem',
			},
			{
				'label': 'Due Date',
				'type': 'Date',
				'key': 'due_date',
				'width': '8rem',
			},
			{
				'label': 'Assigned To',
				'type': 'Link',
				'key': 'assigned_to',
				'width': '10rem',
			},
			{
				'label': 'Last Modified',
				'type': 'Datetime',
				'key': 'modified',
				'width': '8rem',
			},
		]

		rows = [
			"name",
			"title",
			"description",
			"assigned_to",
			"due_date",
			"status",
			"priority",
			"reference_doctype",
			"reference_docname",
			"modified",
		]
		return {'columns': columns, 'rows': rows}

	@staticmethod
	def default_kanban_settings():
		return {
			"column_field": "status",
			"title_field": "title",
			"kanban_fields": '["description", "priority", "creation"]'
		}
