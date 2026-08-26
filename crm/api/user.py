import frappe
from frappe import _
from frappe.auth import LoginAttemptTracker
from frappe.rate_limiter import rate_limit
from frappe.utils.password import check_password, update_password


@frappe.whitelist()
@rate_limit(limit=5, seconds=300)  # 5 attempts per 5 minutes per user/IP
def change_password(old_password: str, new_password: str):
	"""
	Change password for the current logged-in user.
	Uses Frappe's LoginAttemptTracker for attempt counting/lockout, and rate_limit for API abuse protection.
	"""
	user = frappe.session.user
	if user == "Guest":
		frappe.throw(_("You must be logged in to change your password"), frappe.AuthenticationError)

	tracker = LoginAttemptTracker(user)
	if not tracker.is_user_allowed():
		frappe.throw(_("Too many failed attempts. Please try again after some time."))

	if old_password == new_password:
		frappe.throw(
			_("New password cannot be the same as current password. Please choose a different password.")
		)

	try:
		check_password(user, old_password)
	except frappe.AuthenticationError:
		tracker.add_failure_attempt()
		frappe.throw(_("Incorrect current password. Please try again."))
	else:
		tracker.add_success_attempt()

	# Validate new password strength (server-side enforcement)
	from frappe.core.doctype.user.user import test_password_strength

	result = test_password_strength(new_password)
	feedback = result.get("feedback", {})
	if not feedback.get("password_policy_validation_passed", False):
		suggestions = feedback.get("suggestions", [])
		frappe.throw(_("Password is too weak. {0}").format(" ".join(suggestions) if suggestions else ""))

	update_password(user=user, pwd=new_password, logout_all_sessions=False)
	return _("Password Updated Successfully")


def needs_password_setup() -> bool:
	"""Whether the session user has no password of their own and must set one.

	True for users provisioned without a password — the Frappe Cloud site owner,
	users created by a script — who are logged into a session they never
	authenticated for and so have no way back in once it expires.

	Users who sign in through SSO are excluded: having no password is the
	correct state for them, not something to fix.
	"""
	user = frappe.session.user

	# Checked first: it is the discriminating one, and it short-circuits the
	# other queries for everyone who already has a password — which is almost
	# everyone, on every CRM page load.
	if has_password(user):
		return False

	if frappe.get_system_settings("disable_user_pass_login"):
		return False

	# Every user carries a `frappe` provider row (Frappe issues one on insert
	# so the site can act as an identity provider), so only other providers
	# mean the user actually signs in through SSO.
	if frappe.db.exists(
		"User Social Login",
		{
			"parenttype": "User",
			"parent": user,
			"provider": ["!=", "frappe"],
			"userid": ["is", "set"],
		},
	):
		return False

	return True


def has_password(user: str) -> bool:
	"""Whether a password is stored for the user.

	User passwords are hashed rows in `__Auth` with `encrypted = 0`, so
	`get_decrypted_password` (which only looks at encrypted rows) cannot answer
	this — hence the direct query.
	"""
	Auth = frappe.qb.Table("__Auth")

	return bool(
		(
			frappe.qb.from_(Auth)
			.select(Auth.name)
			.where(
				(Auth.doctype == "User")
				& (Auth.name == user)
				& (Auth.fieldname == "password")
				& (Auth.encrypted == 0)
			)
			.limit(1)
		).run()
	)


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
		node = frappe.db.get_value(
			"CRM Sales Hierarchy", {"user": user}, ["name", "reports_to"], as_dict=True
		)
		if node:
			has_reports = frappe.db.exists("CRM Sales Hierarchy", {"reports_to": node.name})
			if has_reports or not node.reports_to:
				frappe.throw(
					_("Remove this user from the sales hierarchy before changing their role to Sales User")
				)
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
	if "System Manager" in roles and current_user_is_system_manager:
		remove_roles(user_doc, "System Manager")
		update_module_in_user(user_doc, "FCRM")

	user_doc.save(ignore_permissions=True)

	node_name = frappe.db.get_value("CRM Sales Hierarchy", {"user": user}, "name")
	if node_name:
		frappe.delete_doc("CRM Sales Hierarchy", node_name, ignore_permissions=True)

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
