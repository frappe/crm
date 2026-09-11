import frappe
from frappe.tests import IntegrationTestCase

from crm.patches.v1_0.dedupe_task_call_log_links import execute
from crm.tests.test_integrations import create_test_call_log


class TestDedupeTaskCallLogLinks(IntegrationTestCase):
	def tearDown(self):
		frappe.db.rollback()

	def test_keeps_the_call_closest_to_the_tasks_creation(self):
		task = frappe.get_doc(
			{
				"doctype": "CRM Task",
				"title": "Legacy duplicate task",
				"status": "Todo",
				"priority": "Medium",
			}
		).insert()

		first_call = create_test_call_log()
		first_call.append("links", {"link_doctype": "CRM Task", "link_name": task.name})
		first_call.save()

		second_call = create_test_call_log()
		second_call.append("links", {"link_doctype": "CRM Task", "link_name": task.name})
		second_call.save()

		execute()

		first_call.reload()
		second_call.reload()

		first_call_tasks = [link.link_name for link in first_call.links if link.link_doctype == "CRM Task"]
		second_call_tasks = [link.link_name for link in second_call.links if link.link_doctype == "CRM Task"]

		self.assertIn(str(task.name), first_call_tasks)
		self.assertNotIn(str(task.name), second_call_tasks)

	def test_keeps_the_originating_call_even_when_it_sorts_later_by_creation(self):
		# `older_call` predates the task, so its Dynamic Link row's creation (copied
		# from `older_call`'s own creation - see the patch's docstring) sorts earlier
		# than the task's own creation. `newer_call` is created right after the task,
		# same as `add_task_to_call_log` does, so it's the true originating call even
		# though its link's creation sorts later. A patch that just kept the earliest
		# `Dynamic Link.creation` would wrongly keep `older_call` here.
		older_call = create_test_call_log()

		task = frappe.get_doc(
			{
				"doctype": "CRM Task",
				"title": "Task originating from a later call",
				"status": "Todo",
				"priority": "Medium",
			}
		).insert()

		newer_call = create_test_call_log()

		newer_call.append("links", {"link_doctype": "CRM Task", "link_name": task.name})
		newer_call.save()

		older_call.append("links", {"link_doctype": "CRM Task", "link_name": task.name})
		older_call.save()

		execute()

		newer_call.reload()
		older_call.reload()

		newer_call_tasks = [link.link_name for link in newer_call.links if link.link_doctype == "CRM Task"]
		older_call_tasks = [link.link_name for link in older_call.links if link.link_doctype == "CRM Task"]

		self.assertIn(str(task.name), newer_call_tasks)
		self.assertNotIn(str(task.name), older_call_tasks)

	def test_leaves_single_links_untouched(self):
		task = frappe.get_doc(
			{
				"doctype": "CRM Task",
				"title": "Single-linked task",
				"status": "Todo",
				"priority": "Medium",
			}
		).insert()

		call_log = create_test_call_log()
		call_log.append("links", {"link_doctype": "CRM Task", "link_name": task.name})
		call_log.save()

		execute()

		call_log.reload()
		call_log_tasks = [link.link_name for link in call_log.links if link.link_doctype == "CRM Task"]
		self.assertIn(str(task.name), call_log_tasks)
