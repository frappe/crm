# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from bs4 import BeautifulSoup
from frappe.desk.form.assign_to import add as assign
from frappe.desk.form.assign_to import remove as unassign
from frappe.model.document import Document


class CRMTask(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		assigned_to: DF.Link | None
		description: DF.TextEditor | None
		due_date: DF.Datetime | None
		name: DF.Int | None
		priority: DF.Literal["Low", "Medium", "High"]
		reference_docname: DF.DynamicLink | None
		reference_doctype: DF.Link | None
		start_date: DF.Date | None
		status: DF.Literal["Backlog", "Todo", "In Progress", "Done", "Canceled"]
		title: DF.Data
	# end: auto-generated types

	def after_insert(self):
		self.assign_to()

	def on_update(self):
		self.attach_description_images()

	def attach_description_images(self):
		if not self.description:
			return

		file_urls = {
			image["src"]
			for image in BeautifulSoup(self.description, "html.parser").find_all("img", src=True)
			if image["src"].startswith(("/files/", "/private/files/"))
		}
		if not file_urls:
			return

		# Only claim the current user's uploads that are not already attached elsewhere.
		files = frappe.get_all(
			"File",
			filters={
				"file_url": ["in", list(file_urls)],
				"owner": frappe.session.user,
				"attached_to_doctype": ["is", "not set"],
				"attached_to_name": ["is", "not set"],
				"attached_to_field": ["is", "not set"],
			},
			fields=["name", "file_url"],
		)
		for file in files:
			# File URLs are case-sensitive even when the database comparison is not.
			if file.file_url in file_urls:
				frappe.db.set_value(
					"File",
					file.name,
					{
						"attached_to_doctype": self.doctype,
						"attached_to_name": self.name,
						"attached_to_field": "description",
					},
				)

	def validate(self):
		if self.is_new() or not self.assigned_to:
			return

		if self.get_doc_before_save().assigned_to != self.assigned_to:
			self.unassign_from_previous_user(self.get_doc_before_save().assigned_to)
			self.assign_to()

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
