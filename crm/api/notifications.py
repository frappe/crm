from html import unescape

import frappe
from frappe.query_builder import Order
from frappe.utils import strip_html_tags

from crm.fcrm.doctype.crm_notification.crm_notification import get_record_title

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

	senders = get_reply_senders(notifications)
	titles = {}

	_notifications = []
	for notification in notifications:
		record = (notification.reference_doctype, notification.reference_name)
		if notification.reference_name and record not in titles:
			titles[record] = get_record_title(*record)
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
				"title": titles.get(record),
				"sender": senders.get(notification.notification_type_doc)
				or (notification.type == "Mention" and full_names.get(notification.from_user))
				or None,
				"preview": get_preview(notification),
				"route_name": ("Deal" if notification.reference_doctype == "CRM Deal" else "Lead"),
			}
		)

	return _notifications


def get_reply_senders(notifications) -> dict:
	# Customers are rarely users, so the name comes from the email or WhatsApp message.
	docs = {"Communication": [], "WA Message": []}
	for n in notifications:
		if n.type == "Reply" and n.notification_type_doctype in docs:
			docs[n.notification_type_doctype].append(n.notification_type_doc)

	senders = {}
	if docs["Communication"]:
		for c in frappe.get_all(
			"Communication",
			filters={"name": ["in", docs["Communication"]]},
			fields=["name", "sender_full_name", "sender"],
		):
			senders[c.name] = c.sender_full_name or c.sender
	if docs["WA Message"]:
		profiles = frappe.qb.DocType("WA Profile")
		messages = frappe.qb.DocType("WA Message")
		for m in (
			frappe.qb.from_(messages)
			.left_join(profiles)
			.on(profiles.name == messages.to)
			.select(messages.name, profiles.profile_name, profiles.phone_number)
			.where(messages.name.isin(docs["WA Message"]))
		).run(as_dict=True):
			senders[m.name] = m.profile_name or m.phone_number
	return senders


def get_preview(notification) -> str:
	# The message itself for replies and mentions, what happened for everything else.
	has_message = notification.type in ("Reply", "Mention", "WhatsApp")
	text = (has_message and notification.message) or notification.notification_text or ""
	return " ".join(unescape(strip_html_tags(text)).split())[:200]


@frappe.whitelist()
def get_unread_count() -> int:
	return frappe.db.count("CRM Notification", {"to_user": frappe.session.user, "read": 0})


@frappe.whitelist()
def mark_as_read(doc: str | None = None, docs: list[str] | None = None):
	"""Mark the user's unread notifications as read with a single update.

	Saving them one by one sent a realtime event per notification, and every
	open tab reloaded the list for each event.
	"""
	user = frappe.session.user
	filters = {"to_user": user, "read": 0}
	docs = [doc] if doc else docs
	if docs:
		names = frappe.get_all(
			"CRM Notification",
			filters=filters,
			or_filters={"comment": ["in", docs], "notification_type_doc": ["in", docs]},
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
		# "<tab>/<row>" opens the tab and scrolls to the comment or note.
		tab = "notes" if notification.notification_type_doctype == "FCRM Note" else "comments"
		_hash = f"#{tab}/{notification.notification_type_doc}"

	if notification.type == "WhatsApp" or (
		notification.type == "Reply" and notification.notification_type_doctype == "WA Message"
	):
		_hash = "#whatsapp"

	if notification.type == "Booking":
		_hash = "#events"

	if notification.type == "Reply" and notification.notification_type_doctype == "Communication":
		_hash = "#emails"

	if notification.type == "Reminder":
		_hash = "#tasks"

	if notification.type == "Assignment" and notification.notification_type_doctype == "CRM Task":
		_hash = "#tasks"
		if "has been removed by" in notification.message:
			_hash = ""
	return _hash
