from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from crm.api.notifications import (
	NOTIFICATIONS_PAGE_LENGTH,
	get_notifications,
	get_unread_count,
	mark_as_read,
)

USER1 = "crm.user1@example.com"
USER2 = "crm.user2@example.com"
SENDER = "crm.admin@example.com"


def make_notification(to_user, **kwargs):
	doc = frappe.get_doc(
		{
			"doctype": "CRM Notification",
			"from_user": SENDER,
			"to_user": to_user,
			"type": "Mention",
			"message": "mentioned you",
			**kwargs,
		}
	)
	doc.flags.ignore_links = True
	return doc.insert(ignore_permissions=True)


class TestNotificationsAPI(IntegrationTestCase):
	def setUp(self):
		frappe.db.delete("CRM Notification", {"to_user": ["in", [USER1, USER2]]})

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def test_list_is_capped_and_newest_first(self):
		for _ in range(NOTIFICATIONS_PAGE_LENGTH + 5):
			make_notification(USER1)

		frappe.set_user(USER1)
		notifications = get_notifications()

		self.assertEqual(len(notifications), NOTIFICATIONS_PAGE_LENGTH)
		creations = [n["creation"] for n in notifications]
		self.assertEqual(creations, sorted(creations, reverse=True))

	def test_list_shows_only_own_notifications_with_sender_name(self):
		make_notification(USER1)
		make_notification(USER2)

		frappe.set_user(USER1)
		notifications = get_notifications()

		self.assertEqual({n["to_user"] for n in notifications}, {USER1})
		self.assertEqual(
			notifications[0]["from_user"]["full_name"], frappe.db.get_value("User", SENDER, "full_name")
		)

	def test_unread_count_includes_notifications_past_the_page(self):
		for _ in range(NOTIFICATIONS_PAGE_LENGTH + 5):
			make_notification(USER1)
		make_notification(USER1, read=1)

		frappe.set_user(USER1)
		self.assertEqual(get_unread_count(), NOTIFICATIONS_PAGE_LENGTH + 5)

	def test_mark_all_as_read_touches_only_own_and_sends_one_event(self):
		for _ in range(3):
			make_notification(USER1)
		make_notification(USER2)

		frappe.set_user(USER1)
		with patch("crm.api.notifications.frappe.publish_realtime") as publish:
			mark_as_read()

		self.assertEqual(get_unread_count(), 0)
		self.assertEqual(frappe.db.count("CRM Notification", {"to_user": USER2, "read": 0}), 1)
		publish.assert_called_once_with("crm_notification", user=USER1, after_commit=True)

	def test_mark_one_doc_as_read(self):
		make_notification(USER1, notification_type_doctype="Comment", notification_type_doc="COMMENT-1")
		make_notification(USER1, notification_type_doctype="Comment", notification_type_doc="COMMENT-2")

		frappe.set_user(USER1)
		mark_as_read("COMMENT-1")

		unread = frappe.get_all(
			"CRM Notification", {"to_user": USER1, "read": 0}, pluck="notification_type_doc"
		)
		self.assertEqual(unread, ["COMMENT-2"])

	def test_mark_unknown_doc_as_read_changes_nothing(self):
		make_notification(USER1)

		frappe.set_user(USER1)
		mark_as_read("NO-SUCH-COMMENT")

		self.assertEqual(get_unread_count(), 1)

	def test_row_carries_record_title_sender_and_plain_preview(self):
		deal = frappe.get_doc({"doctype": "CRM Deal", "organization_name": "Pratham Tech"})
		deal.flags.ignore_mandatory = True
		deal.insert(ignore_permissions=True)
		organization = frappe.db.get_value("CRM Deal", deal.name, "organization")
		email = frappe.get_doc(
			{
				"doctype": "Communication",
				"communication_type": "Communication",
				"sent_or_received": "Received",
				"subject": "Re: Pricing",
				"sender": "asha@example.com",
				"sender_full_name": "Asha Rao",
			}
		).insert(ignore_permissions=True)
		make_notification(
			USER1,
			type="Reply",
			from_user=None,
			message="Re: Pricing &amp; <b>seats</b>",
			notification_type_doctype="Communication",
			notification_type_doc=email.name,
			reference_doctype="CRM Deal",
			reference_name=deal.name,
		)

		frappe.set_user(USER1)
		row = get_notifications()[0]

		self.assertEqual(row["title"], organization or deal.name)
		self.assertEqual(row["sender"], "Asha Rao")
		self.assertEqual(row["preview"], "Re: Pricing & seats")

	def test_preview_falls_back_to_notification_text(self):
		make_notification(
			USER1,
			type="Assignment",
			message="raw message",
			notification_text='<div class="mb-2"><span>Ankush assigned you a task</span></div>',
		)

		frappe.set_user(USER1)
		row = get_notifications()[0]

		self.assertEqual(row["preview"], "Ankush assigned you a task")
		self.assertIsNone(row["sender"])

	def test_mark_several_docs_as_read(self):
		for name in ("MSG-1", "MSG-2", "MSG-3"):
			make_notification(USER1, notification_type_doctype="Comment", notification_type_doc=name)

		frappe.set_user(USER1)
		mark_as_read(docs=["MSG-1", "MSG-2"])

		unread = frappe.get_all(
			"CRM Notification", {"to_user": USER1, "read": 0}, pluck="notification_type_doc"
		)
		self.assertEqual(unread, ["MSG-3"])

	def test_mention_links_to_its_tab_and_row(self):
		make_notification(USER1, notification_type_doctype="Comment", notification_type_doc="COMMENT-1")
		make_notification(USER1, notification_type_doctype="FCRM Note", notification_type_doc="NOTE-1")

		frappe.set_user(USER1)
		hashes = {n["notification_type_doc"]: n["hash"] for n in get_notifications()}

		self.assertEqual(hashes, {"COMMENT-1": "#comments/COMMENT-1", "NOTE-1": "#notes/NOTE-1"})
