import frappe
from frappe.contacts.doctype.contact.contact import Contact
from frappe.utils import cint


class CustomContact(Contact):
	def validate(self):
		self.add_rows_for_primary_fields()
		super().validate()

	def add_rows_for_primary_fields(self):
		"""Contact takes `email_id`, `phone` and `mobile_no` from its child tables and clears them
		when the tables are empty, so a value set directly on them, as an import does, would be lost."""
		if not (self.is_new() or frappe.flags.in_import):
			return

		if self.email_id and not self.email_ids:
			self.append("email_ids", {"email_id": self.email_id, "is_primary": 1})

		if not self.phone_nos:
			if self.phone:
				self.append(
					"phone_nos",
					{
						"phone": self.phone,
						"is_primary_phone": 1,
						"is_primary_mobile_no": cint(self.phone == self.mobile_no),
					},
				)
			if self.mobile_no and self.mobile_no != self.phone:
				self.append("phone_nos", {"phone": self.mobile_no, "is_primary_mobile_no": 1})

	@staticmethod
	def default_list_data():
		columns = [
			{
				"label": "Name",
				"type": "Data",
				"key": "full_name",
				"width": "17rem",
			},
			{
				"label": "Email",
				"type": "Data",
				"key": "email_id",
				"width": "12rem",
			},
			{
				"label": "Phone",
				"type": "Data",
				"key": "mobile_no",
				"width": "12rem",
			},
			{
				"label": "Organization",
				"type": "Data",
				"key": "company_name",
				"width": "12rem",
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
			"full_name",
			"company_name",
			"email_id",
			"mobile_no",
			"modified",
			"image",
		]
		return {"columns": columns, "rows": rows}
