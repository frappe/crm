import frappe


@frappe.whitelist()
def add_existing_users(users, role="Sales User"):
	"""
	Add existing users to the CRM by assigning them a role.
	:param users: List of user names to be added
	:param role: Role to assign (Customer Service, Sales Agent, Purchase Agent, Sales Team Lead, Purchase Team Lead, Manager, System Manager)
	"""
	frappe.only_for(["System Manager", "Sales Manager"])
	users = frappe.parse_json(users)

	for user in users:
		add_user(user, role)


@frappe.whitelist()
def update_user_role(user, new_role):
	"""
	Update the role of the user.
	:param user: The name of the user
	:param new_role: The new role to assign (Customer Service, Sales Agent, Purchase Agent, Sales Team Lead, Purchase Team Lead, Manager, System Manager)
	"""

	frappe.only_for(["System Manager", "Sales Manager"])

	if new_role not in ["System Manager", "Sales Manager", "Sales User", "Customer Service", "Sales Agent", "Purchase Agent", "Sales Team Lead", "Purchase Team Lead", "Manager"]:
		frappe.throw("Cannot assign this role")

	user_doc = frappe.get_doc("User", user)

	if new_role == "System Manager":
		user_doc.append_roles("System Manager", "Sales Manager", "Sales User")
		user_doc.set("block_modules", [])
	elif new_role == "Manager":
		user_doc.append_roles("Manager", "Sales Manager", "Sales User")
		user_doc.remove_roles("System Manager")
	elif new_role == "Sales Manager":
		user_doc.append_roles("Sales Manager", "Sales User")
		user_doc.remove_roles("System Manager")
	elif new_role in ["Customer Service", "Sales Agent", "Purchase Agent", "Sales Team Lead", "Purchase Team Lead"]:
		user_doc.append_roles(new_role, "Sales User")
		user_doc.remove_roles("Sales Manager", "System Manager")
		update_module_in_user(user_doc, "FCRM")
	elif new_role == "Sales User":
		user_doc.append_roles("Sales User")
		user_doc.remove_roles("Sales Manager", "System Manager")
		update_module_in_user(user_doc, "FCRM")

	user_doc.save(ignore_permissions=True)


@frappe.whitelist()
def add_user(user, role):
	"""
	Add a user means adding role (Sales User or/and Sales Manager) to the user.
	:param user: The name of the user to be added
	:param role: The role to be assigned (Sales User or Sales Manager)
	"""
	update_user_role(user, role)


@frappe.whitelist()
def remove_user(user):
	"""
	Remove a user means removing Sales User & Sales Manager roles from the user.
	:param user: The name of the user to be removed
	"""
	frappe.only_for(["System Manager", "Sales Manager"])

	user_doc = frappe.get_doc("User", user)
	roles = [d.role for d in user_doc.roles]

	# Remove CRM-specific roles
	crm_roles = ["Sales User", "Sales Manager", "Customer Service", "Sales Agent", "Purchase Agent", "Sales Team Lead", "Purchase Team Lead", "Manager"]
	
	for role in crm_roles:
		if role in roles:
			user_doc.remove_roles(role)

	user_doc.save(ignore_permissions=True)
	frappe.msgprint(f"User {user} has been removed from CRM roles.")


def update_module_in_user(user, module):
	block_modules = frappe.get_all(
		"Module Def",
		fields=["name as module"],
		filters={"name": ["!=", module]},
	)

	if block_modules:
		user.set("block_modules", block_modules)
