# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.desk.form.assign_to import add as assign, remove as unassign
from next_crm.ncrm.doctype.crm_notification.crm_notification import notify_user
from frappe.desk.doctype.todo.todo import ToDo


class ToDo(ToDo):
	# def after_insert(self):
	# 	# self.assign_to()
	# 	pass

	# def validate(self):
	# 	if self.is_new() or not self.allocated_to:
	# 		return

	# 	if self.get_doc_before_save().allocated_to != self.allocated_to:
	# 		self.unassign_from_previous_user(self.get_doc_before_save().allocated_to)
	# 		# self.assign_to()
	# 	super().validate()

	# def unassign_from_previous_user(self, user):
	# 	unassign(self.doctype, self.name, user)

	# def assign_to(self):
	# 	if self.allocated_to:
	# 		assign({
	# 			"assign_to": [self.allocated_to],
	# 			"doctype": self.doctype,
	# 			"name": self.name,
	# 			"description": self.custom_title or self.description,
	# 		})


	@staticmethod
	def default_list_data():
		columns = [
			{
				'label': 'Title',
				'type': 'Data',
				'key': 'custom_title',
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
				'key': 'date',
				'width': '8rem',
			},
			{
				'label': 'Assigned To',
				'type': 'Link',
				'key': 'allocated_to',
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
			"custom_title",
			"description",
			"allocated_to",
			"date",
			"status",
			"priority",
			"reference_type",
			"reference_name",
			"modified",
		]
		return {'columns': columns, 'rows': rows}

	@staticmethod
	def default_kanban_settings():
		return {
			"column_field": "status",
			"title_field": "custom_title",
			"kanban_fields": '["description", "priority", "creation"]'
		}
