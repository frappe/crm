import frappe
from frappe.desk.form.activity import get_activity_timeline
from frappe.tests import IntegrationTestCase

from crm.api import record

OTHER_USER = "crm.user1@example.com"


class TestRecordActivities(IntegrationTestCase):
	"""crm.api.record.get_activities wraps Frappe's timeline and adds notes and tasks when asked."""

	def test_returns_frappes_timeline_unchanged(self):
		todo = create_todo()
		todo.add_comment("Comment", "Spoke to them")
		add_reference("FCRM Note", todo)

		result = record.get_activities("ToDo", todo.name)

		self.assertEqual(result, get_activity_timeline("ToDo", todo.name))
		self.assertIn("comment", [row["type"] for row in result["activities"]])
		self.assertNotIn("note", [row["type"] for row in result["activities"]])

	def test_adds_notes_and_tasks_when_asked(self):
		todo = create_todo()
		note = add_reference("FCRM Note", todo)
		task = add_reference("CRM Task", todo)

		rows = record.get_activities("ToDo", todo.name, with_notes_and_tasks=True)["activities"]

		by_key = {row["key"]: row for row in rows}
		self.assertEqual(by_key[f"note:{note.name}"]["data"]["title"], note.title)
		self.assertEqual(by_key[f"task:{task.name}"]["type"], "task")
		self.assertEqual(by_key[f"task:{task.name}"]["author"], by_key["creation"]["author"])
		self.assertEqual(rows, sorted(rows, key=lambda row: (row["timestamp"], row["key"])))

	def test_leaves_out_notes_and_tasks_of_another_doctype_with_the_same_name(self):
		todo = create_todo()
		add_reference("FCRM Note", todo, reference_doctype="CRM Lead")
		add_reference("CRM Task", todo, reference_doctype="CRM Lead")

		rows = record.get_activities("ToDo", todo.name, with_notes_and_tasks=True)["activities"]

		self.assertFalse({"note", "task"} & {row["type"] for row in rows})

	def test_passes_visible_types_to_frappe(self):
		todo = create_todo()
		todo.add_comment("Comment", "Spoke to them")

		rows = record.get_activities("ToDo", todo.name, visible_types=["comment"])["activities"]

		self.assertEqual({row["type"] for row in rows}, {"comment"})

	def test_refuses_a_record_the_user_cannot_read(self):
		todo = create_todo()

		with self.set_user(OTHER_USER), self.assertRaises(frappe.PermissionError):
			record.get_activities("ToDo", todo.name, with_notes_and_tasks=True)


def create_todo():
	return frappe.get_doc(doctype="ToDo", description="Record activities test").insert()


def add_reference(doctype, doc, reference_doctype=None):
	return frappe.get_doc(
		doctype=doctype,
		title=f"{doctype} on {doc.name}",
		reference_doctype=reference_doctype or doc.doctype,
		reference_docname=doc.name,
	).insert(ignore_links=bool(reference_doctype))
