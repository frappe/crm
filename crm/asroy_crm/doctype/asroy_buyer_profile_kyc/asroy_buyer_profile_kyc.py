# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from frappe.model.document import Document


class AsroyBuyerProfileKYC(Document):
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