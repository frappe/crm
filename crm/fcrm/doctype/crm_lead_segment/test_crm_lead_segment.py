# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase

from crm.fcrm.doctype.crm_lead_segment.crm_lead_segment import (
	add_leads,
	get_segment_leads,
	remove_leads,
)

CRM_USER = "crm.user1@example.com"


class TestCRMLeadSegment(IntegrationTestCase):
	def tearDown(self) -> None:
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def test_segment_is_named_after_segment_name(self):
		segment = create_test_segment(segment_name="Hot Prospects")

		self.assertEqual(segment.name, "Hot Prospects")
		self.assertEqual(segment.segment_name, "Hot Prospects")

	def test_assigned_to_accepts_a_crm_user(self):
		segment = create_test_segment(assigned_to=CRM_USER)

		self.assertEqual(segment.assigned_to, CRM_USER)

	def test_assigned_to_rejects_a_non_crm_user(self):
		outsider = create_test_user("segment.outsider@example.com")

		with self.assertRaises(frappe.ValidationError):
			create_test_segment(assigned_to=outsider)

	# ------------------------------------------------------------------
	# Uniqueness -- a lead belongs to a segment at most once
	# ------------------------------------------------------------------

	def test_same_lead_appended_twice_is_rejected(self):
		lead = create_test_lead()
		segment = create_test_segment()

		segment.append("leads", {"lead": lead.name})
		segment.append("leads", {"lead": lead.name})

		with self.assertRaises(frappe.ValidationError):
			segment.save()

	def test_duplicate_row_is_rejected_by_the_database(self):
		"""The unique index is the real guarantee, not just validate()."""
		lead = create_test_lead()
		segment = create_test_segment()
		add_leads(segment.name, [lead.name])

		duplicate = frappe.get_doc(
			{
				"doctype": "CRM Lead Segment Leads",
				"parent": segment.name,
				"parenttype": "CRM Lead Segment",
				"parentfield": "leads",
				"lead": lead.name,
				"idx": 2,
			}
		)

		with self.assertRaises(frappe.UniqueValidationError):
			duplicate.db_insert()

	def test_a_lead_can_belong_to_two_segments(self):
		lead = create_test_lead()
		first = create_test_segment(segment_name="First Segment")
		second = create_test_segment(segment_name="Second Segment")

		add_leads(first.name, [lead.name])
		add_leads(second.name, [lead.name])

		self.assertEqual(get_segment_leads(first.name)["total_count"], 1)
		self.assertEqual(get_segment_leads(second.name)["total_count"], 1)

	def test_add_leads_skips_existing_members_but_adds_the_rest(self):
		existing, fresh = create_test_lead(), create_test_lead()
		segment = create_test_segment()
		add_leads(segment.name, [existing.name])

		result = add_leads(segment.name, [existing.name, fresh.name])

		self.assertEqual(result["added"], 1)
		self.assertEqual(result["skipped"], 1)
		self.assertEqual(result["total"], 2)

	def test_add_leads_collapses_a_lead_repeated_within_one_batch(self):
		lead = create_test_lead()
		segment = create_test_segment()

		result = add_leads(segment.name, [lead.name, lead.name])

		self.assertEqual(result["added"], 1)
		self.assertEqual(result["total"], 1)

	# ------------------------------------------------------------------
	# add / remove / read
	# ------------------------------------------------------------------

	def test_add_leads_skips_a_lead_that_does_not_exist(self):
		lead = create_test_lead()
		segment = create_test_segment()

		result = add_leads(segment.name, [lead.name, "CRM-LEAD-does-not-exist"])

		self.assertEqual(result["added"], 1)
		self.assertEqual(result["skipped"], 1)

	def test_remove_leads_removes_only_the_named_leads(self):
		kept, dropped = create_test_lead(), create_test_lead()
		segment = create_test_segment()
		add_leads(segment.name, [kept.name, dropped.name])

		result = remove_leads(segment.name, [dropped.name])

		self.assertEqual(result["removed"], 1)
		self.assertEqual(result["total"], 1)
		self.assertEqual(get_segment_leads(segment.name)["data"][0].name, kept.name)

	def test_removing_a_lead_does_not_delete_it(self):
		lead = create_test_lead()
		segment = create_test_segment()
		add_leads(segment.name, [lead.name])

		remove_leads(segment.name, [lead.name])

		self.assertTrue(frappe.db.exists("CRM Lead", lead.name))

	def test_get_segment_leads_paginates(self):
		leads = [create_test_lead() for _ in range(3)]
		segment = create_test_segment()
		add_leads(segment.name, [lead.name for lead in leads])

		page = get_segment_leads(segment.name, start=0, page_length=2)

		self.assertEqual(page["total_count"], 3)
		self.assertEqual(page["row_count"], 2)
		self.assertTrue(any(column["key"] == "lead_name" for column in page["columns"]))

	def test_add_leads_is_not_allowed_without_write_permission(self):
		lead = create_test_lead()
		segment = create_test_segment()
		outsider = create_test_user("segment.reader@example.com")

		frappe.set_user(outsider)
		with self.assertRaises(frappe.PermissionError):
			add_leads(segment.name, [lead.name])


def create_test_segment(**kwargs):
	data = {"doctype": "CRM Lead Segment", "segment_name": "Test Segment"}
	data.update(kwargs)
	return frappe.get_doc(data).insert()


def create_test_lead(**kwargs):
	data = {"doctype": "CRM Lead", "first_name": "Segment", "last_name": "Lead"}
	data.update(kwargs)
	doc = frappe.get_doc(data)
	doc.flags.ignore_mandatory = True
	return doc.insert(ignore_permissions=True)


def create_test_user(email):
	if not frappe.db.exists("User", email):
		frappe.get_doc({"doctype": "User", "email": email, "first_name": email.split("@")[0]}).insert(
			ignore_permissions=True
		)
	return email
