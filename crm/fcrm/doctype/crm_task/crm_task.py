# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class CRMTask(Document):
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
