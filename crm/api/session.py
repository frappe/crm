import frappe


@frappe.whitelist()
def get_user_info():
	user = frappe.db.get_value("User", frappe.session.user, ["name", "full_name", "first_name", "last_name", "user_image", ], as_dict=1)
	return user