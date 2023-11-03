import frappe


@frappe.whitelist()
def get_users():
	if frappe.session.user == "Guest":
		frappe.throw("Authentication failed", exc=frappe.AuthenticationError)

	users = frappe.qb.get_query(
		"User",
		fields=["name", "email", "enabled", "user_image", "full_name", "user_type"],
		order_by="full_name asc",
		distinct=True,
	).run(as_dict=1)

	for user in users:
		if frappe.session.user == user.name:
			user.session_user = True
	return users

@frappe.whitelist()
def get_contacts():
	if frappe.session.user == "Guest":
		frappe.throw("Authentication failed", exc=frappe.AuthenticationError)

	contacts = frappe.qb.get_query(
		"Contact",
		fields=['name', 'first_name', 'last_name', 'full_name', 'image', 'email_id', 'mobile_no', 'phone', 'salutation', 'company_name'],
		order_by="first_name asc",
		distinct=True,
	).run(as_dict=1)

	return contacts

@frappe.whitelist()
def get_organizations():
	if frappe.session.user == "Guest":
		frappe.throw("Authentication failed", exc=frappe.AuthenticationError)

	organizations = frappe.qb.get_query(
		"CRM Organization",
		fields=['name', 'organization_logo', 'website'],
		order_by="name asc",
		distinct=True,
	).run(as_dict=1)

	return organizations
