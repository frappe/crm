from unittest.mock import patch

import frappe
from frappe.desk.doctype.todo.todo import ToDo
from frappe.desk.form.activity import get_activity_timeline
from frappe.tests import IntegrationTestCase

from crm.api import record
from crm.api.additional_activities import get_note_rows, get_task_rows

OTHER_USER = "crm.user1@example.com"


def notes_and_tasks(doc):
	return get_note_rows(doc) + get_task_rows(doc)


class TestRecordActivities(IntegrationTestCase):
	"""crm.api.record.get_activities wraps Frappe's timeline and adds the controller's rows."""

	def test_without_a_controller_method_returns_frappes_timeline_unchanged(self):
		todo = create_todo()
		todo.add_comment("Comment", "Spoke to them")
		add_reference("FCRM Note", todo)

		result = record.get_activities("ToDo", todo.name)

		self.assertEqual(result, get_activity_timeline("ToDo", todo.name))
		self.assertNotIn("note", [row["type"] for row in result["activities"]])

	@patch.object(ToDo, "get_additional_activities", notes_and_tasks, create=True)
	def test_adds_the_controllers_rows_in_order(self):
		todo = create_todo()
		note = add_reference("FCRM Note", todo)
		task = add_reference("CRM Task", todo)

		rows = record.get_activities("ToDo", todo.name)["activities"]

		by_key = {row["key"]: row for row in rows}
		self.assertEqual(by_key[f"note:{note.name}"]["data"]["title"], note.title)
		self.assertEqual(by_key[f"task:{task.name}"]["type"], "task")
		self.assertEqual(by_key[f"task:{task.name}"]["author"], by_key["creation"]["author"])
		self.assertEqual(rows, sorted(rows, key=lambda row: (row["timestamp"], row["key"])))

	@patch.object(ToDo, "get_additional_activities", notes_and_tasks, create=True)
	def test_reads_without_writing(self):
		todo = create_todo()
		add_reference("FCRM Note", todo)

		writes = frappe.db.transaction_writes
		record.get_activities("ToDo", todo.name)
		self.assertEqual(frappe.db.transaction_writes, writes)

	@patch.object(ToDo, "get_additional_activities", notes_and_tasks, create=True)
	def test_leaves_out_notes_and_tasks_of_another_doctype_with_the_same_name(self):
		todo = create_todo()
		add_reference("FCRM Note", todo, reference_doctype="CRM Lead")
		add_reference("CRM Task", todo, reference_doctype="CRM Lead")

		rows = record.get_activities("ToDo", todo.name)["activities"]

		self.assertFalse({"note", "task"} & {row["type"] for row in rows})

	@patch.object(ToDo, "get_additional_activities", notes_and_tasks, create=True)
	def test_visible_types_filter_the_controllers_rows_too(self):
		todo = create_todo()
		todo.add_comment("Comment", "Spoke to them")
		add_reference("FCRM Note", todo)
		add_reference("CRM Task", todo)

		comments = record.get_activities("ToDo", todo.name, visible_types=["comment"])["activities"]
		notes = record.get_activities("ToDo", todo.name, visible_types=["note"])["activities"]

		self.assertEqual({row["type"] for row in comments}, {"comment"})
		self.assertEqual({row["type"] for row in notes}, {"note"})

	def test_a_row_frappe_already_returned_is_not_repeated(self):
		todo = create_todo()
		creation = get_activity_timeline("ToDo", todo.name)["activities"][0]

		with patch.object(ToDo, "get_additional_activities", lambda doc: [creation], create=True):
			rows = record.get_activities("ToDo", todo.name)["activities"]

		self.assertEqual([row["key"] for row in rows].count(creation["key"]), 1)

	def test_refuses_a_record_the_user_cannot_read(self):
		todo = create_todo()

		with self.set_user(OTHER_USER), self.assertRaises(frappe.PermissionError):
			record.get_activities("ToDo", todo.name)


def create_todo():
	return frappe.get_doc(doctype="ToDo", description="Record activities test").insert()


def add_reference(doctype, doc, reference_doctype=None):
	return frappe.get_doc(
		doctype=doctype,
		title=f"{doctype} on {doc.name}",
		reference_doctype=reference_doctype or doc.doctype,
		reference_docname=doc.name,
	).insert(ignore_links=bool(reference_doctype))
