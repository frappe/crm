# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase


class TestCRMTask(FrappeTestCase):
	def tearDown(self) -> None:
		frappe.set_user("Administrator")
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

		# Verify task was assigned to exactly one user
		assignees = task.get_assigned_users()
		self.assertEqual(assignees, {"Administrator"})

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

	def test_task_priority_ordering(self):
		"""Test that tasks can be ordered by priority for proper display"""
		# Create tasks with different priorities
		low_task = create_test_task(
			title="Low Priority Task",
			priority="Low",
			status="Todo",
		)
		medium_task = create_test_task(
			title="Medium Priority Task",
			priority="Medium",
			status="Todo",
		)
		high_task = create_test_task(
			title="High Priority Task",
			priority="High",
			status="Todo",
		)

		# Verify priorities are set
		self.assertEqual(low_task.priority, "Low")
		self.assertEqual(medium_task.priority, "Medium")
		self.assertEqual(high_task.priority, "High")

		# Test priority-based filtering
		high_priority_tasks = frappe.get_all(
			"CRM Task",
			filters={"priority": "High", "status": "Todo"},
			fields=["name", "priority"],
		)

		# Verify high priority task is in filtered results
		high_task_names = [t.name for t in high_priority_tasks]
		self.assertIn(high_task.name, high_task_names)
		self.assertNotIn(low_task.name, high_task_names)

	def test_task_status_workflow_and_filtering(self):
		"""Test task status transitions and filtering by status"""
		statuses = ["Backlog", "Todo", "In Progress", "Done", "Canceled"]

		task = create_test_task(title="Status Workflow Task", status="Backlog")
		initial_name = task.name

		# Test status transitions up to Done
		for status in statuses[1:4]:  # Backlog -> Todo -> In Progress -> Done
			task.status = status
			task.save()
			task.reload()
			self.assertEqual(task.status, status)

		# Test filtering by completed status (task should be Done now)
		done_tasks = frappe.get_all("CRM Task", filters={"status": "Done"}, fields=["name"])
		done_task_names = [str(t.name) for t in done_tasks]
		self.assertIn(str(initial_name), done_task_names)

		# Test filtering by active statuses (excluding Done and Canceled)
		task2 = create_test_task(title="Active Task", status="In Progress")
		active_tasks = frappe.get_all(
			"CRM Task",
			filters={"status": ["in", ["Backlog", "Todo", "In Progress"]]},
			fields=["name"],
		)
		active_task_names = [str(t.name) for t in active_tasks]
		self.assertIn(str(task2.name), active_task_names)
		self.assertNotIn(str(initial_name), active_task_names)  # task is Done, not active

		# Test Canceled status separately
		task3 = create_test_task(title="Canceled Task", status="Canceled")
		canceled_tasks = frappe.get_all("CRM Task", filters={"status": "Canceled"}, fields=["name"])
		canceled_task_names = [str(t.name) for t in canceled_tasks]
		self.assertIn(str(task3.name), canceled_task_names)

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

	def test_checklist_progress_and_completion_audit(self):
		task = create_test_task(
			title="Buy vegetables",
			status="Todo",
			checklist=[
				{"item": "Potatoes"},
				{"item": "Tomatoes"},
				{"item": "Okra"},
			],
		)

		self.assertEqual(task.total_items, 3)
		self.assertEqual(task.completed_items, 0)
		self.assertEqual(task.progress, 0)

		task.checklist[0].status = "Completed"
		task.save()
		task.reload()
		self.assertEqual(task.completed_items, 1)
		self.assertAlmostEqual(task.progress, 33.33, places=2)
		self.assertEqual(task.checklist[0].completed_by, "Administrator")
		self.assertTrue(task.checklist[0].completed_on)

		for item in task.checklist:
			item.status = "Completed"
		task.save()
		task.reload()
		self.assertEqual(task.progress, 100)
		self.assertEqual(task.status, "Done")

		task.checklist[1].status = "Pending"
		task.save()
		task.reload()
		self.assertEqual(task.status, "In Progress")
		self.assertIsNone(task.checklist[1].completed_by)
		self.assertIsNone(task.checklist[1].completed_on)

	def test_role_assignment_clears_individual_assignee(self):
		task = create_test_task(
			title="Shared sales task",
			assignment_type="Role",
			assigned_role="Sales User",
			assigned_to="Administrator",
		)

		self.assertEqual(task.assignment_type, "Role")
		self.assertEqual(task.assigned_role, "Sales User")
		self.assertFalse(task.assigned_to)

	def test_task_visibility_for_creator_assignee_and_role(self):
		creator = make_test_user("task-creator@example.com", "Sales Manager")
		assignee = make_test_user("task-assignee@example.com", "Sales User")
		other_manager = make_test_user("other-manager@example.com", "Sales Manager")

		frappe.set_user(creator)
		user_task = create_test_task(title="Private user task", assigned_to=assignee)
		role_task = create_test_task(
			title="Sales role task",
			assignment_type="Role",
			assigned_role="Sales User",
		)

		self.assertTrue(frappe.has_permission("CRM Task", "read", user=user_task.owner, doc=user_task))
		self.assertTrue(frappe.has_permission("CRM Task", "read", user=assignee, doc=user_task))
		self.assertFalse(frappe.has_permission("CRM Task", "read", user=other_manager, doc=user_task))
		self.assertTrue(frappe.has_permission("CRM Task", "read", user=assignee, doc=role_task))
		self.assertFalse(frappe.has_permission("CRM Task", "read", user=other_manager, doc=role_task))

		frappe.set_user(assignee)
		visible_names = set(frappe.get_list("CRM Task", pluck="name"))
		self.assertIn(user_task.name, visible_names)
		self.assertIn(role_task.name, visible_names)

		frappe.set_user(other_manager)
		visible_names = set(frappe.get_list("CRM Task", pluck="name"))
		self.assertNotIn(user_task.name, visible_names)
		self.assertNotIn(role_task.name, visible_names)


def create_test_task(**kwargs):
	"""Helper function to create a CRM Task for testing"""
	data = {"doctype": "CRM Task"}
	data.update(kwargs)
	return frappe.get_doc(data).insert()


def make_test_user(email, role):
	if frappe.db.exists("User", email):
		user = frappe.get_doc("User", email)
	else:
		user = frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": email.split("@")[0],
				"send_welcome_email": 0,
			}
		).insert(ignore_permissions=True)
	if role not in {row.role for row in user.roles}:
		user.append("roles", {"role": role})
		user.save(ignore_permissions=True)
	return email
