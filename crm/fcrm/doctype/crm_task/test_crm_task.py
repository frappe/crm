# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase


class TestCRMTask(IntegrationTestCase):
	def tearDown(self) -> None:
		frappe.db.rollback()

	def test_task_creation(self):
		"""Test creating a basic task"""
		task = create_test_task(
			title="Test Task",
			description="Test task description",
			status="Todo",
			priority="Medium",
		)

		self.assertTrue(task.name)
		self.assertEqual(task.title, "Test Task")
		self.assertEqual(task.status, "Todo")
		self.assertEqual(task.priority, "Medium")

	def test_task_assignment_on_creation(self):
		"""Test that task is assigned to user on creation"""
		task = create_test_task(
			title="Assigned Task",
			assigned_to="Administrator",
		)

		# Verify task was assigned
		assignees = task.get_assigned_users()
		self.assertIn("Administrator", assignees)

	def test_update_assigned_user(self):
		"""Test updating assigned user unassigns previous and assigns new user"""
		# Create test user if not exists
		if not frappe.db.exists("User", "test@example.com"):
			frappe.get_doc(
				{
					"doctype": "User",
					"email": "test@example.com",
					"first_name": "Test",
				}
			).insert()

		# Create task with initial assignment
		task = create_test_task(
			title="Reassign Task",
			assigned_to="Administrator",
		)

		# Verify initial assignment
		assignees = task.get_assigned_users()
		self.assertIn("Administrator", assignees)

		# Get fresh copy of the document to avoid timestamp mismatch
		task = frappe.get_doc("CRM Task", task.name)

		# Change assigned user
		task.assigned_to = "test@example.com"
		task.save()

		# Verify new assignment
		task.reload()
		self.assertEqual(task.assigned_to, "test@example.com")
		assignees_after = task.get_assigned_users()
		self.assertIn("test@example.com", assignees_after)
		self.assertNotIn("Administrator", assignees_after)

	def test_task_with_reference_doctype(self):
		"""Test creating task with reference to another document"""
		# Create a deal for reference
		org = frappe.get_doc(
			{
				"doctype": "CRM Organization",
				"organization_name": "Task Reference Org",
			}
		).insert()

		deal = frappe.get_doc(
			{
				"doctype": "CRM Deal",
				"organization": org.name,
			}
		).insert()

		# Create task with reference
		task = create_test_task(
			title="Deal Task",
			reference_doctype="CRM Deal",
			reference_docname=deal.name,
		)

		self.assertEqual(task.reference_doctype, "CRM Deal")
		self.assertEqual(task.reference_docname, deal.name)

	def test_task_due_date(self):
		"""Test task with due date"""
		task = create_test_task(
			title="Due Date Task",
			due_date="2026-12-31 23:59:59",
			start_date="2026-01-01",
		)

		self.assertTrue(task.due_date)
		self.assertTrue(task.start_date)

	def test_task_priority_levels(self):
		"""Test different priority levels"""
		priorities = ["Low", "Medium", "High"]

		for priority in priorities:
			task = create_test_task(
				title=f"{priority} Priority Task",
				priority=priority,
			)
			self.assertEqual(task.priority, priority)

	def test_task_status_workflow(self):
		"""Test task status transitions"""
		statuses = ["Backlog", "Todo", "In Progress", "Done", "Canceled"]

		task = create_test_task(title="Status Workflow Task", status="Backlog")

		for status in statuses[1:]:
			task.status = status
			task.save()
			task.reload()
			self.assertEqual(task.status, status)

	def test_task_without_assigned_user(self):
		"""Test creating task without assigned user"""
		task = create_test_task(title="Unassigned Task")

		self.assertFalse(task.assigned_to)
		assignees = task.get_assigned_users()
		self.assertEqual(len(assignees), 0)

	def test_task_description(self):
		"""Test task with rich text description"""
		description = "<p>This is a <strong>rich text</strong> description</p>"
		task = create_test_task(
			title="Description Task",
			description=description,
		)

		self.assertEqual(task.description, description)

	def test_reassign_to_same_user(self):
		"""Test that reassigning to same user doesn't create duplicate assignments"""
		task = create_test_task(
			title="Same User Task",
			assigned_to="Administrator",
		)

		initial_assignees = task.get_assigned_users()
		initial_count = len(initial_assignees)

		# Get fresh copy of the document to avoid timestamp mismatch
		task = frappe.get_doc("CRM Task", task.name)

		# Save again without changing assigned_to
		task.save()

		# Verify no duplicate assignments
		task.reload()
		assignees_after = task.get_assigned_users()
		self.assertEqual(len(assignees_after), initial_count)
		self.assertIn("Administrator", assignees_after)


def create_test_task(**kwargs):
	"""Helper function to create a CRM Task for testing"""
	data = {"doctype": "CRM Task"}
	data.update(kwargs)
	return frappe.get_doc(data).insert()
