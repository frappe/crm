# Copyright (c) 2025, Glascutr Ltd and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class AsroySellerProfileKYC(Document):
	@staticmethod
	def default_list_data():
		columns = [
			{
				"label": "Name",
				"type": "data",
				"key": "name1",
				"width": "9rem",
			},
			{
				"label": "Email",
				"type": "data",
				"key": "email",
				"width": "9rem",
			},
			{
				"label": "Mobile",
				"type": "data",
				"key": "mobile",
				"width": "9rem",
			},
		]
		rows = [
			"name",
			"email",
			"mobile",
		]
		return {"columns": columns, "rows": rows}