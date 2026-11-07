# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe
from frappe.client import set_value
from frappe.share import add_docshare
from frappe.tests import IntegrationTestCase

OWNER = "note-owner@example.com"
OTHER = "note-other@example.com"
MANAGER = "note-manager@example.com"


class TestFCRMNote(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		make_user(OWNER, "Sales User")
		make_user(OTHER, "Sales User")
		make_user(MANAGER, "Sales Manager")

	def setUp(self):
		frappe.db.savepoint("test_fcrm_note")
		self.lead = make_record("CRM Lead", lead_owner=OWNER, first_name="Note", email=None)
		self.deal = make_record("CRM Deal", deal_owner=OWNER, organization="Note Org")
		self.lead_note = make_note("CRM Lead", self.lead.name)
		self.deal_note = make_note("CRM Deal", self.deal.name)
		self.unlinked_note = make_note()

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback(save_point="test_fcrm_note")

	def listed_notes(self, user):
		frappe.set_user(user)
		return set(frappe.get_list("FCRM Note", pluck="name", limit_page_length=0))

	def test_notes_listed_follow_the_record(self):
		listed = self.listed_notes(OWNER)
		self.assertLessEqual({self.lead_note.name, self.deal_note.name, self.unlinked_note.name}, listed)

		listed = self.listed_notes(OTHER)
		self.assertIn(self.unlinked_note.name, listed)
		self.assertNotIn(self.lead_note.name, listed)
		self.assertNotIn(self.deal_note.name, listed)

	def test_note_with_another_reference_keeps_role_access(self):
		note = make_note(
			"CRM Organization", make_record("CRM Organization", organization_name="Note Org").name
		)
		self.assertIn(note.name, self.listed_notes(OTHER))
		self.assertTrue(frappe.has_permission("FCRM Note", "read", note.name, user=OTHER))

	def test_manager_sees_every_note(self):
		self.assertLessEqual(
			{self.lead_note.name, self.deal_note.name, self.unlinked_note.name}, self.listed_notes(MANAGER)
		)

	def test_assignee_can_read_note(self):
		frappe.get_doc(
			{
				"doctype": "ToDo",
				"description": "Follow up",
				"reference_type": "CRM Lead",
				"reference_name": self.lead.name,
				"allocated_to": OTHER,
			}
		).insert(ignore_permissions=True)
		self.assertIn(self.lead_note.name, self.listed_notes(OTHER))
		self.assertTrue(frappe.has_permission("FCRM Note", "read", self.lead_note.name, user=OTHER))

	def test_shared_record_shares_its_notes(self):
		add_docshare("CRM Lead", self.lead.name, OTHER, read=1, flags={"ignore_share_permission": True})
		self.assertIn(self.lead_note.name, self.listed_notes(OTHER))
		self.assertTrue(frappe.has_permission("FCRM Note", "read", self.lead_note.name, user=OTHER))

	def test_note_cannot_be_opened_or_changed_without_the_record(self):
		for ptype in ("read", "write", "delete"):
			self.assertFalse(frappe.has_permission("FCRM Note", ptype, self.lead_note.name, user=OTHER))
			self.assertFalse(frappe.has_permission("FCRM Note", ptype, self.deal_note.name, user=OTHER))
			self.assertTrue(frappe.has_permission("FCRM Note", ptype, self.lead_note.name, user=OWNER))
			self.assertTrue(frappe.has_permission("FCRM Note", ptype, self.unlinked_note.name, user=OTHER))

	def test_note_cannot_be_added_to_an_unreadable_record(self):
		frappe.set_user(OTHER)
		with self.assertRaises(frappe.PermissionError):
			make_note("CRM Lead", self.lead.name, ignore_permissions=False)

		frappe.set_user(OWNER)
		make_note("CRM Lead", self.lead.name, ignore_permissions=False)

	def test_note_cannot_be_moved_to_a_readable_record_to_read_it(self):
		own_lead = make_record("CRM Lead", lead_owner=OTHER, first_name="Other", email=None)

		frappe.set_user(OTHER)
		with self.assertRaises(frappe.PermissionError):
			set_value("FCRM Note", self.lead_note.name, "reference_docname", own_lead.name)

		frappe.set_user("Administrator")
		self.assertEqual(
			frappe.db.get_value("FCRM Note", self.lead_note.name, "reference_docname"), self.lead.name
		)

	def test_mention_notifies_only_people_who_can_read_the_record(self):
		frappe.set_user(OWNER)
		note = make_note("CRM Lead", self.lead.name, content=mention(OTHER) + mention(MANAGER))

		notified = frappe.get_all(
			"CRM Notification",
			filters={
				"type": "Mention",
				"notification_type_doctype": "FCRM Note",
				"notification_type_doc": note.name,
			},
			pluck="to_user",
		)
		self.assertEqual(notified, [MANAGER])


def make_user(email, role):
	if not frappe.db.exists("User", email):
		frappe.get_doc(
			{"doctype": "User", "email": email, "first_name": email.split("@")[0], "send_welcome_email": 0}
		).insert(ignore_permissions=True)
	frappe.get_doc("User", email).add_roles(role)


def make_record(doctype, **fields):
	doc = frappe.get_doc({"doctype": doctype, **fields})
	doc.flags.ignore_mandatory = True
	doc.flags.ignore_links = True
	return doc.insert(ignore_permissions=True)


def make_note(reference_doctype=None, reference_docname=None, content="", ignore_permissions=True):
	return frappe.get_doc(
		{
			"doctype": "FCRM Note",
			"title": "Test note",
			"content": content,
			"reference_doctype": reference_doctype,
			"reference_docname": reference_docname,
		}
	).insert(ignore_permissions=ignore_permissions)


def mention(email):
	return f'<span class="mention" data-type="mention" data-id="{email}" data-label="{email}">@{email}</span>'
