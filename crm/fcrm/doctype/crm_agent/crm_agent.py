# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class CRMAgent(Document):
	def validate(self):
		if self.user:
			user = frappe.get_doc("User", self.user)
			if not self.first_name:
				self.first_name = user.first_name
			if not self.middle_name:
				self.middle_name = user.middle_name
			if not self.last_name:
				self.last_name = user.last_name
			if not self.agent_name:
				self.agent_name = user.full_name
			if not self.image:
				self.image = user.user_image


@frappe.whitelist()
def update_agent_role(user, new_role):
	"""
	Update the role of the user to Agent
	:param user: The name of the user
	:param new_role: The new role to assign (Sales Manager or Sales User)
	"""

	frappe.only_for("Sales Manager")

	if new_role not in ["Sales Manager", "Sales User"]:
		frappe.throw("Cannot assign this role")

	user_doc = frappe.get_doc("User", user)

	if new_role == "Sales Manager":
		user_doc.append_roles("Sales Manager", "System Manager")
	if new_role == "Sales User":
		user_doc.append_roles("Sales User")
		if "Sales Manager" in frappe.get_roles(user_doc.name):
			user_doc.remove_roles("Sales Manager", "System Manager")

	user_doc.save()


@frappe.whitelist()
def update_agent_status(agent, status):
	"""
	Activate or deactivate the agent
	:param agent: The name of the agent
	:param status: The status to set (1 for active, 0 for inactive)
	"""
	frappe.only_for("Sales Manager")

	frappe.db.set_value("CRM Agent", agent, "is_active", status)
