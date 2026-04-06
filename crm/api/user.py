import frappe
from frappe import _


@frappe.whitelist()
def add_existing_users(users: str | list, role: str = "Sales User"):
	"""
	Add existing users to the CRM by assigning them a role (Sales User or Sales Manager).
	:param users: List of user names to be added
	"""
	frappe.only_for(["System Manager", "Sales Manager"], True)
	is_system_manager = "System Manager" in frappe.get_roles()

	if role == "System Manager" and not is_system_manager:
		frappe.throw(_("Only System Managers can assign the System Manager role"), frappe.PermissionError)

	if role == "Sales Manager" and not is_system_manager:
		frappe.throw(_("Only System Managers can assign the Sales Manager role"), frappe.PermissionError)

	users = frappe.parse_json(users)

	for user in users:
		update_user_role(user, role)


@frappe.whitelist()
def update_user_role(user: str, new_role: str):
	"""
	Update the role of the user to Sales Manager, Sales User, or System Manager.
	:param user: The name of the user
	:param new_role: The new role to assign (Sales Manager or Sales User)
	"""

	frappe.only_for(["System Manager", "Sales Manager"], True)
	is_system_manager = "System Manager" in frappe.get_roles()

	if new_role not in ["System Manager", "Sales Manager", "Sales User"]:
		frappe.throw(_("Cannot assign this role"))

	user_doc = frappe.get_doc("User", user)
	target_roles = [d.role for d in user_doc.roles]
	target_is_system_manager = "System Manager" in target_roles

	if new_role == "System Manager" and not is_system_manager:
		frappe.throw(_("Only System Managers can assign the System Manager role"), frappe.PermissionError)

	if target_is_system_manager and not is_system_manager:
		frappe.throw(_("Only System Managers can modify other System Managers"), frappe.PermissionError)

	if new_role == "Sales Manager" and not is_system_manager:
		frappe.throw(_("Only System Managers can assign the Sales Manager role"), frappe.PermissionError)

	if new_role == "System Manager":
		user_doc.append_roles("System Manager", "Sales Manager", "Sales User")
		user_doc.set("block_modules", [])
	if new_role == "Sales Manager":
		user_doc.append_roles("Sales Manager", "Sales User")
		remove_roles(user_doc, "System Manager")
	if new_role == "Sales User":
		user_doc.append_roles("Sales User")
		remove_roles(user_doc, "Sales Manager", "System Manager")
		update_module_in_user(user_doc, "FCRM")

	user_doc.save(ignore_permissions=True)


@frappe.whitelist()
def remove_crm_roles_from_user(user: str):
	"""
	Remove a user means removing Sales User & Sales Manager roles from the user.
	:param user: The name of the user to be removed
	"""
	frappe.only_for(["System Manager", "Sales Manager"], True)

	if user == frappe.session.user:
		frappe.throw(_("You cannot remove yourself."), frappe.PermissionError)

	user_doc = frappe.get_doc("User", user)
	roles = [d.role for d in user_doc.roles]

	current_user_is_system_manager = "System Manager" in frappe.get_roles()

	if "System Manager" in roles and not current_user_is_system_manager:
		frappe.throw(_("Only System Managers can modify other System Managers"), frappe.PermissionError)

	if user_doc.get("role_profiles") or user_doc.get("role_profile_name"):
		return frappe.throw(
			_("User {0} cannot be removed as it has a Role Profile assigned to it.").format(user)
		)

	if "Sales User" in roles:
		remove_roles(user_doc, "Sales User")
	if "Sales Manager" in roles:
		remove_roles(user_doc, "Sales Manager")

	user_doc.save(ignore_permissions=True)
	frappe.msgprint(_("User {0} has been removed from CRM roles.").format(user))


def remove_roles(self, *roles):
	existing_roles = {d.role: d for d in self.get("roles")}
	for role in roles:
		if role in existing_roles:
			self.get("roles").remove(existing_roles[role])


def update_module_in_user(user, module):
	block_modules = frappe.get_all(
		"Module Def",
		fields=["name as module"],
		filters={"name": ["!=", module]},
	)

	if block_modules:
		user.set("block_modules", block_modules)
