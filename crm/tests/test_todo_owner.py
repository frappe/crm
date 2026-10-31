# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase


def make_user(email, roles=None):
	if not frappe.db.exists("User", email):
		user = frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": email.split("@")[0],
				"send_welcome_email": 0,
			}
		)
		for role in roles or []:
			user.append("roles", {"role": role})
		user.insert(ignore_permissions=True)
	return email


class TestToDoOwnerMirror(FrappeTestCase):
	def setUp(self):
		self.owner = make_user("deal-owner@example.com", ["Sales User"])
		self.attacker = make_user("deal-attacker@example.com", ["Sales User"])
		frappe.set_user("Administrator")
		self.deal = frappe.get_doc(
			{"doctype": "CRM Deal", "first_name": "Owner Test", "deal_owner": self.owner}
		).insert()

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def create_todo(self, as_user, allocated_to, ignore_permissions=False):
		frappe.set_user(as_user)
		frappe.get_doc(
			{
				"doctype": "ToDo",
				"description": "x",
				"status": "Open",
				"reference_type": "CRM Deal",
				"reference_name": self.deal.name,
				"allocated_to": allocated_to,
			}
		).insert(ignore_permissions=ignore_permissions)

	def test_creation_blocked_when_creator_has_no_access(self):
		with self.assertRaises(frappe.PermissionError):
			self.create_todo(as_user=self.attacker, allocated_to=self.attacker)
		self.assertEqual(frappe.db.get_value("CRM Deal", self.deal.name, "deal_owner"), self.owner)

	def test_owner_mirrors_for_trusted_assignment(self):
		self.create_todo(as_user="Administrator", allocated_to=self.attacker, ignore_permissions=True)
		self.assertEqual(frappe.db.get_value("CRM Deal", self.deal.name, "deal_owner"), self.attacker)

	def test_record_owner_can_assign(self):
		self.create_todo(as_user=self.owner, allocated_to=self.owner)
		self.assertEqual(frappe.db.get_value("CRM Deal", self.deal.name, "deal_owner"), self.owner)
