import frappe
from frappe import _

CRM_ALLOWED_ROLES = ["System Manager", "Sales Manager", "Sales User"]


def get_session_role_flags():
	roles = set(frappe.get_roles())

	if not roles.intersection(set(CRM_ALLOWED_ROLES)):
		frappe.throw(_("You are not permitted to access CRM resources."), frappe.PermissionError)

	return {
		"is_system_manager": "System Manager" in roles,
		"is_sales_manager": "Sales Manager" in roles and "System Manager" not in roles,
		"is_sales_user": "Sales User" in roles
		and "Sales Manager" not in roles
		and "System Manager" not in roles,
	}


@frappe.whitelist()
def get_users():
	session_roles = get_session_role_flags()

	users = frappe.qb.get_query(
		"User",
		fields=[
			"name",
			"email",
			"enabled",
			"user_image",
			"first_name",
			"last_name",
			"full_name",
			"user_type",
			"language",
		],
		order_by="full_name asc",
		filters={"enabled": 1},
	).run(as_dict=1)

	if not users:
		return [], []

	user_names = [u.name for u in users]
	system_language = frappe.db.get_single_value("System Settings", "language")
	session_user = frappe.session.user

	role_rows = frappe.get_all(
		"Has Role",
		filters={"parent": ["in", user_names], "parenttype": "User"},
		fields=["parent", "role"],
	)
	roles_by_user = {}
	for row in role_rows:
		roles_by_user.setdefault(row.parent, []).append(row.role)

	telephony_agents = set(
		frappe.get_all(
			"CRM Telephony Agent",
			filters={"user": ["in", user_names]},
			pluck="user",
		)
	)

	role_priority = ("System Manager", "Sales Manager", "Sales User", "Guest")
	crm_users = []

	for user in users:
		if session_user == user.name:
			user.session_user = True

		# Mirror frappe.get_roles() which appends implicit "All" and "Guest"
		user.roles = roles_by_user.get(user.name, []) + ["All", "Guest"]

		user.role = ""
		for role in role_priority:
			if role in user.roles:
				user.role = role
				break

		user.is_telephony_agent = user.name in telephony_agents
		user.language = user.language or system_language

		if user.role in CRM_ALLOWED_ROLES:
			crm_users.append(user)

	if not session_roles["is_system_manager"]:
		users = crm_users

	return users, crm_users


@frappe.whitelist()
def get_organizations():
	get_session_role_flags()

	organizations = frappe.qb.get_query(
		"CRM Organization",
		fields=["*"],
		order_by="name asc",
		distinct=True,
	).run(as_dict=1)

	return organizations
