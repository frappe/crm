# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils.nestedset import rebuild_tree

from crm.permissions.org_hierarchy import (
	get_lead_permission_query_conditions,
	has_deal_permission,
	has_lead_permission,
	hierarchy_enabled,
)


class TestOrgHierarchy(IntegrationTestCase):
	"""
	Hierarchy structure used in tests:
	  manager@hier.test  (root)
	  ├── rep1@hier.test
	  └── rep2@hier.test
	  outsider@hier.test  (not in the hierarchy)
	"""

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		# Create test users
		make_user("manager@hier.test", roles=["Sales Manager"])
		make_user("rep1@hier.test", roles=["Sales User"])
		make_user("rep2@hier.test", roles=["Sales User"])
		make_user("outsider@hier.test", roles=["Sales User"])

		# Build hierarchy
		mgr = make_hierarchy_node("manager@hier.test", is_group=1)
		make_hierarchy_node("rep1@hier.test", reports_to=mgr.name)
		make_hierarchy_node("rep2@hier.test", reports_to=mgr.name)
		rebuild_tree("CRM Sales Hierarchy")

		settings = frappe.get_single("FCRM Settings")
		settings.enable_sales_hierarchy = 1
		settings.save(ignore_permissions=True)

	@classmethod
	def tearDownClass(cls):
		super().tearDownClass()

	def setUp(self):
		frappe.db.savepoint("test_org_hierarchy")

	def tearDown(self):
		frappe.db.rollback(save_point="test_org_hierarchy")

	# ------------------------------------------------------------------
	# hierarchy_enabled
	# ------------------------------------------------------------------

	def test_hierarchy_is_enabled(self):
		self.assertTrue(hierarchy_enabled())

	# ------------------------------------------------------------------
	# Lead permissions -- owner-based
	# ------------------------------------------------------------------

	def test_owner_can_read_own_lead(self):
		lead = make_lead("rep1@hier.test")
		self.assertTrue(has_lead_permission(lead, "read", "rep1@hier.test"))

	def test_manager_can_read_direct_report_lead(self):
		lead = make_lead("rep1@hier.test")
		self.assertTrue(has_lead_permission(lead, "read", "manager@hier.test"))

	def test_manager_can_read_any_report_lead(self):
		lead = make_lead("rep2@hier.test")
		self.assertTrue(has_lead_permission(lead, "read", "manager@hier.test"))

	def test_sibling_cannot_read_peer_lead(self):
		lead = make_lead("rep1@hier.test")
		self.assertFalse(has_lead_permission(lead, "read", "rep2@hier.test"))

	def test_outsider_cannot_read_team_lead(self):
		lead = make_lead("rep1@hier.test")
		self.assertFalse(has_lead_permission(lead, "read", "outsider@hier.test"))

	def test_administrator_always_has_permission(self):
		lead = make_lead("rep1@hier.test")
		self.assertTrue(has_lead_permission(lead, "read", "Administrator"))

	# ------------------------------------------------------------------
	# Lead permissions -- ToDo-based
	# ------------------------------------------------------------------

	def test_direct_assignee_can_read_lead(self):
		lead = make_lead("rep1@hier.test")
		assign_todo("CRM Lead", lead.name, "outsider@hier.test")
		self.assertTrue(has_lead_permission(lead, "read", "outsider@hier.test"))

	def test_cancelled_todo_does_not_grant_access(self):
		lead = make_lead("rep1@hier.test")
		assign_todo("CRM Lead", lead.name, "outsider@hier.test", status="Cancelled")
		self.assertFalse(has_lead_permission(lead, "read", "outsider@hier.test"))

	def test_manager_can_read_lead_assigned_to_report(self):
		lead = make_lead("outsider@hier.test")
		assign_todo("CRM Lead", lead.name, "rep1@hier.test")
		self.assertTrue(has_lead_permission(lead, "read", "manager@hier.test"))

	# ------------------------------------------------------------------
	# Deal permissions
	# ------------------------------------------------------------------

	def test_manager_can_read_report_deal(self):
		deal = make_deal("rep2@hier.test")
		self.assertTrue(has_deal_permission(deal, "read", "manager@hier.test"))

	def test_peer_cannot_read_sibling_deal(self):
		deal = make_deal("rep2@hier.test")
		self.assertFalse(has_deal_permission(deal, "read", "rep1@hier.test"))

	# ------------------------------------------------------------------
	# Permission query conditions
	# ------------------------------------------------------------------

	def test_query_conditions_empty_for_administrator(self):
		self.assertFalse(get_lead_permission_query_conditions("Administrator"))

	def test_query_conditions_non_empty_for_regular_user(self):
		self.assertTrue(get_lead_permission_query_conditions("rep1@hier.test"))

	# ------------------------------------------------------------------
	# Hierarchy disabled
	# ------------------------------------------------------------------

	def test_hierarchy_disabled_allows_outsider_to_read_any_lead(self):
		settings = frappe.get_single("FCRM Settings")
		settings.enable_sales_hierarchy = 0
		settings.save(ignore_permissions=True)
		try:
			lead = make_lead("rep1@hier.test")
			self.assertTrue(has_lead_permission(lead, "read", "outsider@hier.test"))
		finally:
			settings.enable_sales_hierarchy = 1
			settings.save(ignore_permissions=True)

	def test_query_conditions_empty_when_hierarchy_disabled(self):
		settings = frappe.get_single("FCRM Settings")
		settings.enable_sales_hierarchy = 0
		settings.save(ignore_permissions=True)
		try:
			self.assertFalse(get_lead_permission_query_conditions("rep1@hier.test"))
		finally:
			settings.enable_sales_hierarchy = 1
			settings.save(ignore_permissions=True)


def make_user(email, roles=None):
	if frappe.db.exists("User", email):
		return frappe.get_doc("User", email)
	u = frappe.get_doc(
		{
			"doctype": "User",
			"email": email,
			"first_name": email.split("@")[0],
			"send_welcome_email": 0,
		}
	).insert(ignore_permissions=True)
	for role in roles or []:
		u.add_roles(role)
	return u


def make_hierarchy_node(user, reports_to=None, is_group=0):
	existing = frappe.db.get_value("CRM Sales Hierarchy", {"user": user}, "name")
	if existing:
		return frappe.get_doc("CRM Sales Hierarchy", existing)
	return frappe.get_doc(
		{
			"doctype": "CRM Sales Hierarchy",
			"user": user,
			"reports_to": reports_to,
			"is_group": is_group,
		}
	).insert(ignore_permissions=True)


def make_lead(owner_email):
	doc = frappe.get_doc({"doctype": "CRM Lead", "lead_owner": owner_email, "first_name": "Test"})
	doc.flags.ignore_mandatory = True
	return doc.insert(ignore_permissions=True)


def make_deal(owner_email):
	doc = frappe.get_doc({"doctype": "CRM Deal", "deal_owner": owner_email, "organization": "Test Org"})
	doc.flags.ignore_mandatory = True
	doc.flags.ignore_links = True
	return doc.insert(ignore_permissions=True)


def assign_todo(doctype, docname, allocated_to, status="Open"):
	return frappe.get_doc(
		{
			"doctype": "ToDo",
			"reference_type": doctype,
			"reference_name": docname,
			"allocated_to": allocated_to,
			"status": status,
			"description": f"Test assignment to {allocated_to}",
		}
	).insert(ignore_permissions=True)
