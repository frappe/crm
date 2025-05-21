# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class CRMAgent(Document):
	pass


@frappe.whitelist()
def update_agent_role(user, new_role):
	"""
	Update the role of the user to Agent
	"""

	user_doc = frappe.get_doc("User", user)

	if new_role == "Sales Manager":
		user_doc.append_roles("Sales Manager", "System Manager")
	if new_role == "Sales User":
		user_doc.append_roles("Sales User")
		if "Sales Manager" in frappe.get_roles(user_doc.name):
			user_doc.remove_roles("Sales Manager", "System Manager")

	user_doc.save()
