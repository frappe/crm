import frappe

from crm.api.user import FLOW_ROLE
from crm.fcrm.doctype.crm_dashboard.home_scope import sales_users


def execute():
	"""Flow is on by default for CRM users, including those who joined before it. A Role Profile
	decides its users' roles, so an admin adds Flow User there."""
	if not frappe.db.exists("Role", FLOW_ROLE):
		return
	for name in sales_users():
		user = frappe.get_doc("User", name)
		if user.get("role_profiles") or user.get("role_profile_name"):
			continue
		if FLOW_ROLE not in [row.role for row in user.roles]:
			user.add_roles(FLOW_ROLE)
