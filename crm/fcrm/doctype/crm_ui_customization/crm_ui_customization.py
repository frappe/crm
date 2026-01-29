# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import json

import frappe
from frappe.model.document import Document


class CRMUICustomization(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		disabled: DF.Check
		dt: DF.Link | None
		json: DF.JSON | None
		title: DF.Data | None
		type: DF.Literal[
			"Quick Filters",
			"App Sidebar",
			"Quick Entry",
			"Side Panel",
			"Data Fields",
			"Grid Row",
			"Required Fields",
		]
		user: DF.Link | None
	# end: auto-generated types

	def autoname(self):
		self.name = f"{self.type}"
		if self.dt:
			self.name += f" - {self.dt}"
		if self.user:
			self.name += f" - {self.user}"

		self.title = self.name


@frappe.whitelist()
def get_sidebar_layout():
	if frappe.db.exists("CRM UI Customization", {"type": "App Sidebar", "disabled": 0}):
		doc = frappe.get_doc("CRM UI Customization", "App Sidebar")

		if doc and doc.json:
			return json.loads(doc.json)

	return []
