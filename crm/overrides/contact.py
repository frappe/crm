import frappe
from frappe.contacts.doctype.contact.contact import Contact


def contact_on_trash(doc, method=None):
	"""Clean up all dependent/linked records before contact is deleted so LinkExistsError never occurs."""
	name = getattr(doc, "name", None) or str(doc)
	if not name:
		return

	# 1. Clean up CRM Daily Allocation tasks referencing this contact
	frappe.db.delete("CRM Daily Allocation", {"contact": name})

	# 2. Clean up CRM Contacts child table in CRM Deals
	frappe.db.delete("CRM Contacts", {"contact": name})

	# 3. Clear direct contact field on CRM Deals
	frappe.db.set_value("CRM Deal", {"contact": name}, "contact", None)

	# 4. Clean up Dynamic Link records pointing to this contact
	frappe.db.delete("Dynamic Link", {"link_doctype": "Contact", "link_name": name})

	# 5. Clean up CRM Call Log dynamic references
	frappe.db.set_value(
		"CRM Call Log",
		{"reference_doctype": "Contact", "reference_docname": name},
		{"reference_doctype": None, "reference_docname": None},
	)

	# 6. Clean up FCRM Note dynamic references
	frappe.db.set_value(
		"FCRM Note",
		{"reference_doctype": "Contact", "reference_docname": name},
		{"reference_doctype": None, "reference_docname": None},
	)

	# 7. Clean up ToDo assignments for this contact
	frappe.db.delete("ToDo", {"reference_type": "Contact", "reference_name": name})

	# 8. Clean up CRM Notification references
	frappe.db.delete("CRM Notification", {"reference_doctype": "Contact", "reference_name": name})


class CustomContact(Contact):
	def on_trash(self):
		contact_on_trash(self)
		if hasattr(super(), "on_trash"):
			super().on_trash()

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
			"_assign",
			"custom_is_dropped",
		]
		return {"columns": columns, "rows": rows}
