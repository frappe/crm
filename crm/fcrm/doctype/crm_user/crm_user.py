# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class CRMUser(Document):
	def validate(self):
		if self.user:
			user = frappe.get_doc("User", self.user)
			if not self.first_name:
				self.first_name = user.first_name
			if not self.middle_name:
				self.middle_name = user.middle_name
			if not self.last_name:
				self.last_name = user.last_name
			if not self.user_name:
				self.user_name = user.full_name
			if not self.image:
				self.image = user.user_image


@frappe.whitelist()
def add_existing_users(users, role='Sales User'):
	"""
	Add existing users to the CRM User doctype.
	:param users: List of user names to be added
	"""
	frappe.only_for(["System Manager", "Sales Manager"])
	users = frappe.parse_json(users)

	for user in users:
		if not frappe.db.exists("CRM User", {"user": user}):
			new_user = frappe.new_doc("CRM User")
			new_user.user = user
			new_user.save(ignore_permissions=True)

			update_user_role(user, role)
		else:
			frappe.throw(f"User {user} already exists")


@frappe.whitelist()
def update_user_role(user, new_role):
	"""
	Update the role of the user to Sales Manager, Sales User, or System Manager.
	:param user: The name of the user
	:param new_role: The new role to assign (Sales Manager or Sales User)
	"""

	frappe.only_for(["System Manager", "Sales Manager"])

	if new_role not in ["System Manager", "Sales Manager", "Sales User"]:
		frappe.throw("Cannot assign this role")

	user_doc = frappe.get_doc("User", user)

	if new_role == "System Manager":
		user_doc.append_roles("System Manager")
	if new_role == "Sales Manager":
		user_doc.append_roles("Sales Manager")
		user_doc.remove_roles("System Manager")
	if new_role == "Sales User":
		user_doc.append_roles("Sales User")
		user_doc.remove_roles("Sales Manager", "System Manager")

	user_doc.save()


@frappe.whitelist()
def update_user_status(user, status):
	"""
	Activate or deactivate the user
	:param user: The name of the user
	:param status: The status to set (1 for active, 0 for inactive)
	"""
	frappe.only_for(["System Manager", "Sales Manager"])

	frappe.db.set_value("CRM User", user, "is_active", status)
