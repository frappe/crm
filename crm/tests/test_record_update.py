import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_to_date

from crm.api import record

OTHER_USER = "crm.user1@example.com"


class TestUpdateRecord(IntegrationTestCase):
	"""crm.api.record.update_record refuses a save based on a stale `modified`."""

	def test_fresh_save_is_accepted_and_returns_the_new_modified(self):
		todo = create_todo()

		modified = record.update_record("ToDo", todo.name, {"description": "Mine"}, str(todo.modified))

		self.assertEqual(frappe.db.get_value("ToDo", todo.name, "description"), "Mine")
		self.assertEqual(str(frappe.db.get_value("ToDo", todo.name, "modified")), str(modified))
		record.update_record("ToDo", todo.name, {"description": "Mine again"}, modified)
		self.assertEqual(frappe.db.get_value("ToDo", todo.name, "description"), "Mine again")

	def test_stale_save_is_refused(self):
		todo = create_todo()
		frappe.db.set_value(
			"ToDo", todo.name, "description", "Theirs", modified=add_to_date(todo.modified, seconds=1)
		)

		with self.assertRaises(frappe.TimestampMismatchError):
			record.update_record("ToDo", todo.name, {"description": "Mine"}, str(todo.modified))
		self.assertEqual(frappe.db.get_value("ToDo", todo.name, "description"), "Theirs")

	def test_only_writable_fields_are_accepted(self):
		todo = create_todo()

		# standard, internal, read-only and unknown keys
		for values in ({"owner": OTHER_USER}, {"__islocal": 1}, {"assignment_rule": "x"}, {"nope": 1}):
			with self.subTest(values=values), self.assertRaises(frappe.ValidationError):
				record.update_record("ToDo", todo.name, {"description": "Mine", **values}, str(todo.modified))
		self.assertEqual(frappe.db.get_value("ToDo", todo.name, "description"), "Record update test")
		self.assertEqual(frappe.db.count("ToDo", {"description": "Record update test"}), 1)

	def test_refuses_a_record_the_user_cannot_write(self):
		todo = create_todo()

		with self.set_user(OTHER_USER), self.assertRaises(frappe.PermissionError):
			record.update_record("ToDo", todo.name, {"description": "Mine"}, str(todo.modified))


def create_todo():
	return frappe.get_doc(doctype="ToDo", description="Record update test").insert()
