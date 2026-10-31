# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.tests import IntegrationTestCase

from crm.api.user import update_user_role
from crm.tests.test_password_setup import make_user

DOCTYPE = "CRM Sales Hierarchy"


class TestCRMSalesHierarchy(IntegrationTestCase):
	"""The writes the Sales hierarchy settings block sends, under the session user's DocPerms."""

	def setUp(self):
		self.admin = make_user("hierarchy-admin@example.com", roles=["System Manager"])
		self.manager = make_user("hierarchy-manager@example.com", roles=["Sales Manager", "Sales User"])
		self.lead = make_user("hierarchy-lead@example.com", roles=["Sales Manager", "Sales User"])
		self.rep = make_user("hierarchy-rep@example.com", roles=["Sales User"])

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def test_a_sales_manager_reads_the_tree_but_cannot_change_it(self):
		frappe.set_user(self.admin.name)
		self.place(self.manager)
		frappe.set_user(self.manager.name)

		self.assertEqual(len(frappe.get_list(DOCTYPE, filters={"user": self.manager.name})), 1)
		with self.assertRaises(frappe.PermissionError):
			self.place(self.rep)

	def test_moving_a_report_away_lets_their_lead_be_demoted(self):
		frappe.set_user(self.admin.name)
		top = self.place(self.manager)
		lead = self.place(self.lead, top)
		rep = self.place(self.rep, lead)

		with self.assertRaises(frappe.ValidationError):
			update_user_role(self.lead.name, "Sales User")

		self.move(rep, top)
		update_user_role(self.lead.name, "Sales User")
		self.assertNotIn("Sales Manager", frappe.get_roles(self.lead.name))

	def test_removing_a_lead_moves_their_reports_up_first(self):
		frappe.set_user(self.admin.name)
		top = self.place(self.manager)
		lead = self.place(self.lead, top)
		rep = self.place(self.rep, lead)

		with self.assertRaises(frappe.ValidationError):
			frappe.delete_doc(DOCTYPE, lead)

		self.move(rep, top)
		frappe.delete_doc(DOCTYPE, lead)
		self.assertEqual(frappe.db.get_value(DOCTYPE, rep, "reports_to"), top)

	def place(self, user, reports_to=None):
		return frappe.get_doc(doctype=DOCTYPE, user=user.name, reports_to=reports_to).insert().name

	def move(self, name, reports_to):
		doc = frappe.get_doc(DOCTYPE, name)
		doc.reports_to = reports_to
		doc.save()
