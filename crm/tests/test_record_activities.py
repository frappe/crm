import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_to_date

from crm.api import activities, record
from crm.fcrm.doctype.crm_call_log.test_crm_call_log import create_test_lead
from crm.fcrm.doctype.crm_deal.test_crm_deal import create_test_deal

OTHER_USER = "crm.user1@example.com"


class TestRecordActivities(IntegrationTestCase):
	"""crm.api.record.get_activities works on any doctype, here ToDo."""

	def test_timeline_of_a_non_crm_doctype(self):
		todo = create_todo()
		todo.priority = "High"
		# tests skip versions unless asked
		todo.save(ignore_version=False)
		todo.add_comment("Comment", "Spoke to them")
		file = attach_file(todo)
		add_communication(todo)
		note = add_reference("FCRM Note", todo)
		task = add_reference("CRM Task", todo)

		result = record.get_activities("ToDo", todo.name)

		types = {a["activity_type"] for a in result["activities"]}
		self.assertLessEqual(
			{"creation", "changed", "comment", "attachment_log", "communication", "note"}, types
		)
		self.assertEqual([n.name for n in result["notes"]], [note.name])
		self.assertEqual([t.name for t in result["tasks"]], [task.name])
		self.assertEqual([a.name for a in result["attachments"]], [file.name])
		self.assertNotIn("docinfo", frappe.response)

	def test_notes_and_tasks_of_another_doctype_with_the_same_name(self):
		todo = create_todo()
		add_reference("FCRM Note", todo, reference_doctype="CRM Lead")
		add_reference("CRM Task", todo, reference_doctype="CRM Lead")

		result = record.get_activities("ToDo", todo.name)

		self.assertEqual(result["notes"], [])
		self.assertEqual(result["tasks"], [])
		self.assertNotIn("note", [a["activity_type"] for a in result["activities"]])

	def test_refuses_a_record_the_user_cannot_read(self):
		todo = create_todo()

		with self.set_user(OTHER_USER), self.assertRaises(frappe.PermissionError):
			record.get_activities("ToDo", todo.name)

	def test_lead_timeline_is_unchanged(self):
		lead = create_test_lead("Activities", "+919000000101")
		lead.add_comment("Comment", "Lead comment")
		note = add_reference("FCRM Note", lead)

		timeline, _, notes, *_ = activities.get_activities(lead.name)

		types = [a["activity_type"] for a in timeline]
		self.assertEqual(types[-1], "creation")
		self.assertIn("comment", types)
		self.assertIn("note", types)
		self.assertTrue(all(a["is_lead"] for a in timeline))
		self.assertEqual([n.name for n in notes], [note.name])

	def test_deal_timeline_is_unchanged(self):
		deal = create_test_deal(organization="Record Activities Deal Org")
		deal.add_comment("Comment", "Deal comment")

		timeline, *_ = activities.get_activities(deal.name)

		types = [a["activity_type"] for a in timeline]
		self.assertEqual(types[-1], "creation")
		self.assertIn("comment", types)
		self.assertFalse(any(a["is_lead"] for a in timeline))


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
		self.assertEqual(frappe.db.get_value("ToDo", todo.name, "description"), "Record activities test")
		self.assertEqual(frappe.db.count("ToDo", {"description": "Record activities test"}), 1)

	def test_refuses_a_record_the_user_cannot_write(self):
		todo = create_todo()

		with self.set_user(OTHER_USER), self.assertRaises(frappe.PermissionError):
			record.update_record("ToDo", todo.name, {"description": "Mine"}, str(todo.modified))


def create_todo():
	return frappe.get_doc(doctype="ToDo", description="Record activities test").insert()


def add_reference(doctype, doc, reference_doctype=None):
	return frappe.get_doc(
		doctype=doctype,
		title=f"{doctype} on {doc.name}",
		reference_doctype=reference_doctype or doc.doctype,
		reference_docname=doc.name,
	).insert(ignore_links=bool(reference_doctype))


def attach_file(doc):
	return frappe.get_doc(
		doctype="File",
		file_name="record-activities.txt",
		content="hello",
		attached_to_doctype=doc.doctype,
		attached_to_name=doc.name,
	).insert()


def add_communication(doc):
	return frappe.get_doc(
		doctype="Communication",
		communication_type="Communication",
		communication_medium="Email",
		sent_or_received="Received",
		subject="Record activities email",
		content="Hello",
		sender="someone@example.com",
		reference_doctype=doc.doctype,
		reference_name=doc.name,
	).insert(ignore_permissions=True)
