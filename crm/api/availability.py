import frappe
from frappe import _


def validate_user(doc, method=None):
	if doc.is_new() or not doc.has_value_changed("crm_availability"):
		return

	if doc.crm_availability and not frappe.db.get_value(
		"CRM Availability Status", doc.crm_availability, "enabled"
	):
		frappe.throw(_("{0} is not an enabled availability status.").format(doc.crm_availability))

	doc.crm_availability_changed_on = frappe.utils.now()
	doc.crm_availability_changed_by = frappe.session.user


def on_user_update(doc, method=None):
	if doc.get_doc_before_save() and doc.has_value_changed("crm_availability"):
		publish_availability(doc.name)


def publish_availability(user):
	values = frappe.db.get_value(
		"User",
		user,
		["crm_availability", "crm_availability_changed_on", "crm_availability_changed_by"],
		as_dict=True,
	)
	frappe.publish_realtime(
		"crm_availability_updated",
		{"user": user, **values},
		after_commit=True,
	)


def get_user_categories(users):
	"""Map each user to the category of their status; users with no status count as Active."""
	categories = dict(frappe.get_all("CRM Availability Status", fields=["name", "category"], as_list=True))
	statuses = dict(
		frappe.get_all("User", {"name": ["in", users]}, ["name", "crm_availability"], as_list=True)
	)
	return {user: categories.get(statuses.get(user)) or "Active" for user in users}
