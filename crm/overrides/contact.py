# import frappe
from frappe import _
from frappe.contacts.doctype.contact.contact import Contact


class CustomContact(Contact):
	@staticmethod
	def default_list_data():
		columns = [
			{
				'label': 'First Name',
				'type': 'Data',
				'key': 'first_name',
				'width': '10rem',
			},
			{
				'label': 'Last Name',
				'type': 'Data',
				'key': 'last_name',
				'width': '10rem',
			},
			{
				'label': 'Full Name',
				'type': 'Data',
				'key': 'full_name',
				'width': '17rem',
			},
			{
				'label': 'Email',
				'type': 'Data',
				'key': 'email_id',
				'width': '12rem',
			},
			{
				'label': 'Phone',
				'type': 'Data',
				'key': 'mobile_no',
				'width': '12rem',
			},
			{
				'label': 'Organization',
				'type': 'Data',
				'key': 'company_name',
				'width': '12rem',
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
			"first_name",
			"last_name",
			"full_name",
			"company_name",
			"email_id",
			"mobile_no",
			"modified",
			"image",
		]
		return {'columns': columns, 'rows': rows}
