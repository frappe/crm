import frappe


@frappe.whitelist()
def get_users():
	users = frappe.qb.get_query(
		"User",
		fields=["name", "email", "enabled", "user_image", "first_name", "last_name", "full_name", "user_type"],
		order_by="full_name asc",
		distinct=True,
	).run(as_dict=1)

	for user in users:
		if frappe.session.user == user.name:
			user.session_user = True

		user.is_manager = (
			"Sales Manager" in frappe.get_roles(user.name) or user.name == "Administrator"
		)
	return users

@frappe.whitelist()
def get_contacts():
	contacts = frappe.get_all(
		"Contact",
		fields=[
			"name",
			"salutation",
			"first_name",
			"last_name",
			"full_name",
			"gender",
			"address",
			"designation",
			"image",
			"email_id",
			"mobile_no",
			"phone",
			"company_name",
			"modified"
		],
		order_by="first_name asc",
		distinct=True,
	)

	for contact in contacts:
		contact["email_ids"] = frappe.get_all(
			"Contact Email",
			filters={"parenttype": "Contact", "parent": contact.name},
			fields=["name", "email_id", "is_primary"],
		)

		contact["phone_nos"] = frappe.get_all(
			"Contact Phone",
			filters={"parenttype": "Contact", "parent": contact.name},
			fields=["name", "phone", "is_primary_phone", "is_primary_mobile_no"],
		)

	return contacts

@frappe.whitelist()
def get_lead_contacts():
	lead_contacts = frappe.get_all(
		"CRM Lead",
		fields=[
			"name",
			"lead_name",
			"mobile_no",
			"phone",
			"image",
			"modified"
		],
		filters={"converted": 0},
		order_by="lead_name asc",
		distinct=True,
	)

	return lead_contacts

@frappe.whitelist()
def get_organizations():
	organizations = frappe.qb.get_query(
		"CRM Organization",
		fields=['*'],
		order_by="name asc",
		distinct=True,
	).run(as_dict=1)

	return organizations
