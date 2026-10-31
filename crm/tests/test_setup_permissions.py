# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

import frappe
from frappe.permissions import add_permission
from frappe.tests import IntegrationTestCase

from crm.install import add_sales_manager_setup_permissions
from crm.patches.v1_0.add_setup_sidebar_permissions import remove_sales_user_holiday_list_permissions
from crm.tests.test_navigation import make_desk_user


class TestSetupPermissions(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.user = make_desk_user("crm.setup.permissions.user@example.com")
		cls.manager = make_desk_user("crm.setup.permissions.manager@example.com", "Sales Manager")

	def test_a_sales_manager_keeps_assignment_rules_and_email_templates(self):
		for doctype in ("Assignment Rule", "Email Template"):
			for ptype in ("read", "write", "create"):
				self.assertTrue(
					frappe.has_permission(doctype, ptype, user=self.manager), f"{doctype} {ptype}"
				)

	def test_email_accounts_stay_with_the_system_manager(self):
		self.assertFalse(frappe.has_permission("Email Account", "read", user=self.manager))

	def test_a_sales_user_only_reads_email_templates(self):
		self.assertTrue(frappe.has_permission("Email Template", "read", user=self.user))
		self.assertFalse(frappe.has_permission("Email Template", "write", user=self.user))
		for doctype in ("Assignment Rule", "Email Account", "CRM Holiday List"):
			self.assertFalse(frappe.has_permission(doctype, "read", user=self.user), doctype)

	def test_granting_again_adds_no_rule(self):
		"""The patch runs on sites whose install already granted it."""
		add_sales_manager_setup_permissions()

		for doctype in ("Assignment Rule", "Email Template"):
			rules = frappe.get_all("Custom DocPerm", filters={"parent": doctype, "role": "Sales Manager"})
			self.assertEqual(len(rules), 1, doctype)

	def test_a_sites_own_holiday_list_rule_for_sales_users_goes(self):
		add_permission("CRM Holiday List", "Sales User", 0)
		self.assertTrue(frappe.has_permission("CRM Holiday List", "read", user=self.user))

		remove_sales_user_holiday_list_permissions()

		self.assertFalse(frappe.has_permission("CRM Holiday List", "read", user=self.user))
