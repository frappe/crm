# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

import frappe
from frappe.tests import IntegrationTestCase

from crm.api.user import remove_crm_roles_from_user, update_user_role
from crm.tests.test_password_setup import make_user


class TestUserRoles(IntegrationTestCase):
	def setUp(self):
		self.admin = make_user("roles-admin@example.com", roles=["System Manager"])
		self.manager = make_user("roles-manager@example.com", roles=["Sales Manager", "Sales User"])
		self.rep = make_user("roles-rep@example.com", roles=["Sales User"])

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def test_a_system_manager_promotes_a_sales_user_to_sales_manager(self):
		frappe.set_user(self.admin.name)
		update_user_role(self.rep.name, "Sales Manager")

		self.assertIn("Sales Manager", frappe.get_roles(self.rep.name))

	def test_a_sales_manager_may_not_promote_a_sales_user(self):
		frappe.set_user(self.manager.name)

		with self.assertRaises(frappe.PermissionError):
			update_user_role(self.rep.name, "Sales Manager")
		self.assertNotIn("Sales Manager", frappe.get_roles(self.rep.name))

	def test_a_sales_manager_may_not_remove_a_system_manager(self):
		frappe.set_user(self.manager.name)

		with self.assertRaises(frappe.PermissionError):
			remove_crm_roles_from_user(self.admin.name)

	def test_a_sales_manager_removes_a_sales_users_crm_roles(self):
		frappe.set_user(self.manager.name)
		remove_crm_roles_from_user(self.rep.name)

		self.assertNotIn("Sales User", frappe.get_roles(self.rep.name))
