# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe
from frappe.desk.form.assign_to import add as assign_add
from frappe.desk.form.assign_to import remove as assign_remove
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

	def test_reference_change_requires_deal_access(self):
		"""Pointing an existing ToDo at a deal is rejected when the user cannot access it"""
		frappe.set_user(self.attacker)
		todo = frappe.get_doc(
			{"doctype": "ToDo", "description": "Unlinked", "allocated_to": self.attacker}
		).insert()
		todo.reference_type = "CRM Deal"
		todo.reference_name = self.deal.name
		with self.assertRaises(frappe.PermissionError):
			todo.save()

	def test_reassignment_requires_deal_access(self):
		"""Moving a deal's ToDo to another user is rejected when the editor cannot access the deal"""
		todo_name = self.create_deal_todo(allocated_to=self.owner, assigned_by=self.attacker)

		frappe.set_user(self.attacker)
		todo = frappe.get_doc("ToDo", todo_name)
		todo.allocated_to = self.attacker
		with self.assertRaises(frappe.PermissionError):
			todo.save()

	def test_reopening_cancelled_todo_requires_deal_access(self):
		"""A user removed from a deal cannot reopen their cancelled ToDo to get access back"""
		user = make_user("todo-reopen@example.com", ["Sales User"])
		assign_add({"assign_to": [user], "doctype": "CRM Deal", "name": self.deal.name})
		assign_remove("CRM Deal", self.deal.name, user)
		todo_name = frappe.db.get_value("ToDo", {"reference_name": self.deal.name, "allocated_to": user})

		frappe.set_user(user)
		self.assertFalse(frappe.has_permission("CRM Deal", "read", self.deal.name))
		todo = frappe.get_doc("ToDo", todo_name)
		todo.status = "Open"
		with self.assertRaises(frappe.PermissionError):
			todo.save()

	def test_owner_can_reassign_todo(self):
		"""A user who can access the deal may move its ToDo to another user"""
		todo_name = self.create_deal_todo(allocated_to=self.owner, assigned_by=self.owner)

		frappe.set_user(self.owner)
		todo = frappe.get_doc("ToDo", todo_name)
		todo.allocated_to = self.attacker
		todo.save()
		self.assertEqual(frappe.db.get_value("ToDo", todo_name, "allocated_to"), self.attacker)

	def test_other_todo_edits_skip_deal_access(self):
		"""Editing a ToDo without changing its assignment needs no access to the deal"""
		todo_name = self.create_deal_todo(allocated_to=self.attacker)

		frappe.set_user(self.attacker)
		todo = frappe.get_doc("ToDo", todo_name)
		todo.description = "Edited"
		todo.status = "Closed"
		todo.save()

	def create_deal_todo(self, **kwargs):
		"""Create an open ToDo on the deal the way assign_to does, past the permission check"""
		frappe.set_user("Administrator")
		todo = frappe.get_doc(
			{
				"doctype": "ToDo",
				"description": "Assigned",
				"reference_type": "CRM Deal",
				"reference_name": self.deal.name,
			}
			| kwargs
		).insert(ignore_permissions=True)
		return todo.name
