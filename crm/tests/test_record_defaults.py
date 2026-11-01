# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe
from frappe.cache_manager import clear_doctype_map
from frappe.tests import IntegrationTestCase

RECORDS = {
	"CRM Lead": {"status_doctype": "CRM Lead Status", "owner_field": "lead_owner"},
	"CRM Deal": {"status_doctype": "CRM Deal Status", "owner_field": "deal_owner"},
}
REP = "defaults.rep@example.com"
RULE_USER = "defaults.rule@example.com"
WEEKDAYS = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")


class TestRecordDefaults(IntegrationTestCase):
	def setUp(self):
		make_sales_user(REP)
		make_sales_user(RULE_USER)

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()
		for doctype in RECORDS:
			clear_doctype_map("Assignment Rule", doctype)

	def test_new_record_takes_the_first_status_by_position(self):
		for doctype, record in RECORDS.items():
			with self.subTest(doctype=doctype):
				last = last_open_status(record["status_doctype"])
				frappe.db.set_value(record["status_doctype"], last, "position", 0)

				self.assertEqual(insert_as(REP, doctype).status, last)

	def test_new_record_is_owned_by_its_creator(self):
		for doctype, record in RECORDS.items():
			with self.subTest(doctype=doctype):
				doc = insert_as(REP, doctype)

				self.assertEqual(doc.get(record["owner_field"]), REP)
				self.assertTrue(frappe.has_permission(doctype, "read", doc.name, user=REP))

	def test_sent_status_and_owner_stay(self):
		for doctype, record in RECORDS.items():
			with self.subTest(doctype=doctype):
				status = last_open_status(record["status_doctype"])

				doc = insert_as(REP, doctype, status=status, **{record["owner_field"]: RULE_USER})

				self.assertEqual(doc.status, status)
				self.assertEqual(doc.get(record["owner_field"]), RULE_USER)
				self.assertEqual(get_assignees(doctype, doc.name), [RULE_USER])

	def test_assignment_rule_wins_over_the_default_owner(self):
		for doctype, record in RECORDS.items():
			with self.subTest(doctype=doctype):
				make_assignment_rule(doctype, RULE_USER)

				doc = insert_as(REP, doctype)

				self.assertEqual(frappe.db.get_value(doctype, doc.name, record["owner_field"]), RULE_USER)
				self.assertEqual(get_assignees(doctype, doc.name), [RULE_USER])

	def test_guest_insert_gets_no_owner(self):
		for doctype, record in RECORDS.items():
			with self.subTest(doctype=doctype):
				frappe.set_user("Guest")
				doc = new_record(doctype)
				doc.insert(ignore_permissions=True)
				frappe.set_user("Administrator")

				self.assertFalse(doc.get(record["owner_field"]))
				self.assertTrue(doc.status)


def insert_as(user, doctype, **values):
	frappe.set_user(user)
	doc = new_record(doctype, **values)
	doc.insert()
	frappe.set_user("Administrator")
	return doc


def new_record(doctype, **values):
	doc = frappe.new_doc(doctype)
	if doctype == "CRM Lead":
		doc.first_name = "Defaults"
	doc.update(values)
	return doc


def last_open_status(status_doctype):
	"""The last status by `position` that is not Lost, which would ask for a lost reason."""
	return frappe.get_all(
		status_doctype, filters={"type": ["!=", "Lost"]}, pluck="name", order_by="position desc"
	)[0]


def make_sales_user(email):
	if frappe.db.exists("User", email):
		return
	user = frappe.get_doc(
		{"doctype": "User", "email": email, "first_name": email.split("@")[0], "send_welcome_email": 0}
	).insert(ignore_permissions=True)
	user.add_roles("Sales User")


def make_assignment_rule(doctype, user):
	frappe.get_doc(
		{
			"doctype": "Assignment Rule",
			"name": f"Defaults {doctype}",
			"document_type": doctype,
			"priority": 0,
			"assign_condition": "True",
			"rule": "Round Robin",
			"assignment_days": [{"day": day} for day in WEEKDAYS],
			"users": [{"user": user}],
		}
	).insert()


def get_assignees(doctype, name):
	return frappe.parse_json(frappe.db.get_value(doctype, name, "_assign") or "[]")
