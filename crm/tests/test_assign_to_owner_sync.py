# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe
from frappe.desk.form.assign_to import add as assign_add
from frappe.desk.form.assign_to import remove as assign_remove
from frappe.tests import IntegrationTestCase

OWNER_FIELDS = {"CRM Lead": "lead_owner", "CRM Deal": "deal_owner"}
USER1 = "crm.user1@example.com"
USER2 = "crm.user2@example.com"


class TestAssignToOwnerSync(IntegrationTestCase):
	def tearDown(self):
		frappe.db.rollback()

	# Deal: test_crm_deal.test_reassignment_moves_owner
	def test_assigning_without_owner_sets_lead_owner(self):
		name = create_record("CRM Lead")
		self.assertIsNone(get_owner("CRM Lead", name))

		assign("CRM Lead", name, USER1)

		self.assertEqual(get_owner("CRM Lead", name), USER1)

	def test_removing_owner_clears_it_while_others_stay_assigned(self):
		for doctype in OWNER_FIELDS:
			with self.subTest(doctype=doctype):
				name = create_record(doctype, owner=USER1)
				assign(doctype, name, USER2)
				self.assertEqual(get_owner(doctype, name), USER2)

				assign_remove(doctype, name, USER2)

				self.assertIsNone(get_owner(doctype, name))
				self.assertEqual(get_assignees(doctype, name), [USER1])

	# Deal: test_crm_deal.test_removing_any_assignee_clears_owner
	def test_removing_non_owner_clears_lead_owner(self):
		name = create_record("CRM Lead", owner=USER1)
		assign("CRM Lead", name, USER2)

		assign_remove("CRM Lead", name, USER1)

		self.assertIsNone(get_owner("CRM Lead", name))
		self.assertEqual(get_assignees("CRM Lead", name), [USER2])


def create_record(doctype, owner=None):
	doc = frappe.new_doc(doctype)
	doc.set(OWNER_FIELDS[doctype], owner)
	if doctype == "CRM Lead":
		doc.first_name = "Owner Sync"
	return doc.insert().name


def assign(doctype, name, user):
	assign_add({"assign_to": [user], "doctype": doctype, "name": name})


def get_owner(doctype, name):
	return frappe.db.get_value(doctype, name, OWNER_FIELDS[doctype])


def get_assignees(doctype, name):
	return frappe.parse_json(frappe.db.get_value(doctype, name, "_assign") or "[]")
