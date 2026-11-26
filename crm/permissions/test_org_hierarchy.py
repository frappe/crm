# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils.nestedset import rebuild_tree

from crm.api.activities import get_activities
from crm.api.event import get_calendar_people
from crm.permissions.org_hierarchy import (
	get_call_log_permission_query_conditions,
	get_lead_permission_query_conditions,
	has_call_log_permission,
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

	def test_sales_user_can_create_lead(self):
		new_lead = frappe.get_doc({"doctype": "CRM Lead", "lead_owner": "rep1@hier.test"})
		self.assertTrue(has_lead_permission(new_lead, "create", "rep1@hier.test"))

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
	# Deal activities
	# ------------------------------------------------------------------

	def test_deal_activities_skip_lead_the_user_cannot_read(self):
		lead = make_lead("rep2@hier.test")
		deal = make_deal("rep1@hier.test")
		frappe.db.set_value("CRM Deal", deal.name, "lead", lead.name)

		frappe.set_user("rep1@hier.test")
		try:
			activities, calls, notes, tasks, attachments = get_activities(deal.name)
		finally:
			frappe.set_user("Administrator")

		# the deal's own timeline loads instead of the lead check failing the call
		self.assertTrue(any(a["activity_type"] == "creation" for a in activities))

		# the lead's history stays hidden
		self.assertEqual(calls, [])
		self.assertEqual(notes, [])
		self.assertEqual(tasks, [])
		self.assertEqual(attachments, [])

	# ------------------------------------------------------------------
	# Permission query conditions
	# ------------------------------------------------------------------

	def test_query_conditions_empty_for_administrator(self):
		self.assertFalse(get_lead_permission_query_conditions("Administrator"))

	def test_query_conditions_non_empty_for_regular_user(self):
		self.assertTrue(get_lead_permission_query_conditions("rep1@hier.test"))

	def test_report_with_child_table_field_does_not_raise(self):
		make_lead("rep1@hier.test")
		self.assertTrue(get_lead_permission_query_conditions("rep1@hier.test"))
		frappe.set_user("rep1@hier.test")
		try:
			frappe.get_list(
				"CRM Lead",
				fields=["name", "`tabCRM Products`.`amount`"],
				limit_page_length=5,
			)
		finally:
			frappe.set_user("Administrator")

	# ------------------------------------------------------------------
	# Call logs
	# ------------------------------------------------------------------

	def test_caller_and_receiver_can_read_call(self):
		call = make_call_log(caller="rep1@hier.test", receiver="rep2@hier.test")
		self.assertTrue(has_call_log_permission(call, "read", "rep1@hier.test"))
		self.assertTrue(has_call_log_permission(call, "read", "rep2@hier.test"))

	def test_manager_can_read_report_call(self):
		call = make_call_log(caller="rep1@hier.test")
		self.assertTrue(has_call_log_permission(call, "read", "manager@hier.test"))

	def test_peer_cannot_read_sibling_call(self):
		call = make_call_log(caller="rep1@hier.test")
		self.assertFalse(has_call_log_permission(call, "read", "rep2@hier.test"))
		self.assertFalse(has_call_log_permission(call, "read", "outsider@hier.test"))

	def test_call_on_readable_lead_is_readable(self):
		lead = make_lead("rep2@hier.test")
		call = make_call_log(caller="outsider@hier.test", reference=("CRM Lead", lead.name))
		self.assertTrue(has_call_log_permission(call, "read", "rep2@hier.test"))
		self.assertFalse(has_call_log_permission(call, "read", "rep1@hier.test"))

	def test_call_linked_to_readable_deal_is_readable(self):
		deal = make_deal("rep2@hier.test")
		call = make_call_log(caller="outsider@hier.test", link=("CRM Deal", deal.name))
		self.assertTrue(has_call_log_permission(call, "read", "rep2@hier.test"))
		self.assertTrue(has_call_log_permission(call, "read", "manager@hier.test"))
		self.assertFalse(has_call_log_permission(call, "read", "rep1@hier.test"))

	def test_call_log_list_follows_hierarchy(self):
		mine = make_call_log(caller="rep1@hier.test")
		peer = make_call_log(caller="rep2@hier.test")
		frappe.set_user("rep1@hier.test")
		try:
			names = frappe.get_list("CRM Call Log", pluck="name", limit_page_length=0)
		finally:
			frappe.set_user("Administrator")
		self.assertIn(mine.name, names)
		self.assertNotIn(peer.name, names)

	def test_sales_manager_outside_tree_sees_all_calls(self):
		frappe.db.delete("CRM Sales Hierarchy", {"user": "manager@hier.test"})
		self.assertFalse(get_call_log_permission_query_conditions("manager@hier.test"))

	# ------------------------------------------------------------------
	# Calendar people
	# ------------------------------------------------------------------

	def test_calendar_people_follow_hierarchy(self):
		for user, people in (
			("manager@hier.test", ["manager@hier.test", "rep1@hier.test", "rep2@hier.test"]),
			("rep1@hier.test", ["rep1@hier.test"]),
			("outsider@hier.test", ["outsider@hier.test"]),
		):
			frappe.set_user(user)
			try:
				self.assertEqual(get_calendar_people(), people)
			finally:
				frappe.set_user("Administrator")

	# ------------------------------------------------------------------
	# Hierarchy disabled
	# ------------------------------------------------------------------

	def test_hierarchy_disabled_sales_user_still_restricted_to_own(self):
		settings = frappe.get_single("FCRM Settings")
		settings.enable_sales_hierarchy = 0
		settings.save(ignore_permissions=True)
		try:
			lead = make_lead("rep1@hier.test")
			# Sales User default: cannot read another user's lead even when feature is off
			self.assertFalse(has_lead_permission(lead, "read", "outsider@hier.test"))
			# Sales Manager default: sees everything when feature is off
			self.assertTrue(has_lead_permission(lead, "read", "manager@hier.test"))
		finally:
			settings.enable_sales_hierarchy = 1
			settings.save(ignore_permissions=True)

	def test_query_conditions_when_hierarchy_disabled(self):
		settings = frappe.get_single("FCRM Settings")
		settings.enable_sales_hierarchy = 0
		settings.save(ignore_permissions=True)
		try:
			# Sales User still gets a filter (own + assigned)
			self.assertTrue(get_lead_permission_query_conditions("rep1@hier.test"))
			# Sales Manager has no filter (sees everything)
			self.assertFalse(get_lead_permission_query_conditions("manager@hier.test"))
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


def make_call_log(caller=None, receiver=None, reference=None, link=None):
	doc = frappe.get_doc(
		{
			"doctype": "CRM Call Log",
			"id": frappe.generate_hash(length=12),
			"from": "+911234567890",
			"to": "+919876543210",
			"type": "Outgoing",
			"status": "Completed",
			"caller": caller,
			"receiver": receiver,
		}
	)
	if reference:
		doc.reference_doctype, doc.reference_docname = reference
	if link:
		doc.append("links", {"link_doctype": link[0], "link_name": link[1]})
	return doc.insert(ignore_permissions=True)
