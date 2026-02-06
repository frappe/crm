# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.desk.form.assign_to import add as assign
from frappe.model.document import Document


class CRMEnquiry(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		enquiry_owner: DF.Link | None
		first_name: DF.Data
		mobile_no: DF.Data | None
		notes: DF.Text | None
		naming_series: DF.Literal["CRM-ENQ-.YYYY.-"]
		status: DF.Link
	# end: auto-generated types

	def validate(self):
		self.set_title()
		if not self.is_new() and self.has_value_changed("enquiry_owner") and self.enquiry_owner:
			self.share_with_agent(self.enquiry_owner)
			self.assign_agent(self.enquiry_owner)

	def after_insert(self):
		if self.enquiry_owner:
			self.assign_agent(self.enquiry_owner)

	def set_title(self):
		self.title = self.first_name or self.name

	def assign_agent(self, agent):
		if not agent:
			return

		assignees = self.get_assigned_users()
		if assignees:
			for assignee in assignees:
				if agent == assignee:
					return

		assign({"assign_to": [agent], "doctype": "CRM Enquiry", "name": self.name})

	def share_with_agent(self, agent):
		if not agent:
			return

		docshares = frappe.get_all(
			"DocShare",
			filters={"share_name": self.name, "share_doctype": self.doctype},
			fields=["name", "user"],
		)

		shared_with = [d.user for d in docshares] + [agent]

		for user in shared_with:
			if user == agent and not frappe.db.exists(
				"DocShare",
				{"user": agent, "share_name": self.name, "share_doctype": self.doctype},
			):
				frappe.share.add_docshare(
					self.doctype,
					self.name,
					agent,
					write=1,
					flags={"ignore_share_permission": True},
				)
			elif user != agent:
				frappe.share.remove(self.doctype, self.name, user)

	@staticmethod
	def default_list_data():
		columns = [
			{
				"label": "Name",
				"type": "Data",
				"key": "first_name",
				"width": "12rem",
			},
			{
				"label": "Mobile no",
				"type": "Data",
				"key": "mobile_no",
				"width": "11rem",
			},
			{
				"label": "Status",
				"type": "Select",
				"key": "status",
				"width": "8rem",
			},
			{
				"label": "Owner",
				"type": "Link",
				"key": "enquiry_owner",
				"options": "User",
				"width": "10rem",
			},
			{
				"label": "Assigned to",
				"type": "Text",
				"key": "_assign",
				"width": "10rem",
			},
			{
				"label": "Last modified",
				"type": "Datetime",
				"key": "modified",
				"width": "8rem",
			},
		]
		rows = [
			"name",
			"first_name",
			"mobile_no",
			"status",
			"enquiry_owner",
			"modified",
			"_assign",
		]
		return {"columns": columns, "rows": rows}
