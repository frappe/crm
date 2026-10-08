import frappe
from frappe.query_builder import Order

# The panel shows the latest ones; older history is never rendered, and
# loading all of it took seconds for users with thousands of notifications.
NOTIFICATIONS_PAGE_LENGTH = 50


@frappe.whitelist()
def get_notifications():
	Notification = frappe.qb.DocType("CRM Notification")
	notifications = (
		frappe.qb.from_(Notification)
		.select(
			Notification.creation,
			Notification.from_user,
			Notification.to_user,
			Notification.type,
			Notification.read,
			Notification.message,
			Notification.notification_text,
			Notification.notification_type_doctype,
			Notification.notification_type_doc,
			Notification.reference_doctype,
			Notification.reference_name,
		)
		.where(Notification.to_user == frappe.session.user)
		.orderby(Notification.creation, order=Order.desc)
		.limit(NOTIFICATIONS_PAGE_LENGTH)
	).run(as_dict=True)

	from_users = {n.from_user for n in notifications if n.from_user}
	full_names = dict(
		frappe.get_all(
			"User", filters={"name": ["in", list(from_users)]}, fields=["name", "full_name"], as_list=True
		)
	)

	_notifications = []
	for notification in notifications:
		_notifications.append(
			{
				"creation": notification.creation,
				"from_user": {
					"name": notification.from_user,
					"full_name": full_names.get(notification.from_user),
				},
				"type": notification.type,
				"to_user": notification.to_user,
				"read": notification.read,
				"hash": get_hash(notification),
				"notification_text": notification.notification_text,
				"notification_type_doctype": notification.notification_type_doctype,
				"notification_type_doc": notification.notification_type_doc,
				"reference_doctype": ("deal" if notification.reference_doctype == "CRM Deal" else "lead"),
				"reference_name": notification.reference_name,
				"route_name": ("Deal" if notification.reference_doctype == "CRM Deal" else "Lead"),
			}
		)

	return _notifications


@frappe.whitelist()
def get_unread_count() -> int:
	return frappe.db.count("CRM Notification", {"to_user": frappe.session.user, "read": 0})


@frappe.whitelist()
def mark_as_read(doc: str | None = None):
	"""Mark the user's unread notifications as read with a single update.

	Saving them one by one sent a realtime event per notification, and every
	open tab reloaded the list for each event.
	"""
	user = frappe.session.user
	filters = {"to_user": user, "read": 0}
	if doc:
		names = frappe.get_all(
			"CRM Notification",
			filters=filters,
			or_filters={"comment": doc, "notification_type_doc": doc},
			pluck="name",
		)
		if not names:
			return
		filters["name"] = ["in", names]

	frappe.db.set_value("CRM Notification", filters, "read", 1, update_modified=False)
	frappe.publish_realtime("crm_notification", user=user, after_commit=True)


def get_hash(notification):
	_hash = ""
	if notification.type == "Mention" and notification.notification_type_doc:
		_hash = "#" + notification.notification_type_doc

	if notification.type == "WhatsApp":
		_hash = "#whatsapp"

	if notification.type == "Assignment" and notification.notification_type_doctype == "CRM Task":
		_hash = "#tasks"
		if "has been removed by" in notification.message:
			_hash = ""
	return _hash
