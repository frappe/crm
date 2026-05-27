import json

import frappe
from frappe.tests import IntegrationTestCase


class TestMergeLead(IntegrationTestCase):
	def tearDown(self):
		frappe.db.rollback()

	def _create_lead(self, **kwargs):
		data = {"doctype": "CRM Lead"}
		data.update(kwargs)
		return frappe.get_doc(data).insert(ignore_permissions=True)

	def test_find_duplicates_by_email(self):
		lead1 = self._create_lead(first_name="John", last_name="Doe", email="john@test.com")
		lead2 = self._create_lead(first_name="Johnny", email="john@test.com", mobile_no="+111")

		from crm.api.lead import find_duplicate_leads

		dups = find_duplicate_leads(lead2.name)
		names = [d["name"] for d in dups]
		self.assertIn(lead1.name, names)
		for d in dups:
			if d["name"] == lead1.name:
				self.assertIn("email", d["matched_fields"])

	def test_find_duplicates_by_mobile(self):
		lead1 = self._create_lead(first_name="Jane", email="jane@test.com", mobile_no="+999")
		lead2 = self._create_lead(first_name="Janet", mobile_no="+999")

		from crm.api.lead import find_duplicate_leads

		dups = find_duplicate_leads(lead2.name)
		names = [d["name"] for d in dups]
		self.assertIn(lead1.name, names)

	def test_no_self_duplicate(self):
		lead = self._create_lead(first_name="Self", email="self@test.com")

		from crm.api.lead import find_duplicate_leads

		dups = find_duplicate_leads(lead.name)
		self.assertEqual(len(dups), 0)

	def test_merge_leads_basic(self):
		# lead_a: has mobile_no but no phone; lead_b: has phone but no mobile_no
		lead_a = self._create_lead(
			first_name="Target", email="target@test.com", mobile_no="+111", status="New"
		)
		lead_b = self._create_lead(
			first_name="Source", mobile_no="", phone="+333", status="Contacted"
		)

		from crm.api.lead import merge_leads

		result = merge_leads(lead_a.name, lead_b.name)

		self.assertEqual(result["target"], lead_a.name)
		self.assertEqual(result["source"], lead_b.name)

		lead_a.reload()
		lead_b.reload()

		# source non-empty values overwrite target
		self.assertEqual(lead_a.first_name, "Source")
		self.assertEqual(lead_a.status, "Contacted")
		self.assertEqual(lead_a.phone, "+333")
		# source empty mobile_no does NOT overwrite target's value
		self.assertEqual(lead_a.mobile_no, "+111")

		self.assertEqual(lead_b.merged_into, lead_a.name)
		self.assertEqual(lead_b.is_duplicate, 1)

	def test_merge_creates_merge_log(self):
		lead_a = self._create_lead(first_name="A", email="a@test.com")
		lead_b = self._create_lead(first_name="B", email="b@test.com")

		from crm.api.lead import merge_leads

		merge_leads(lead_a.name, lead_b.name)

		log = frappe.get_last_doc("CRM Merge Log", {"reference_doctype": "CRM Lead"})
		self.assertEqual(log.target_document_name, lead_a.name)
		self.assertEqual(log.source_document_name, lead_b.name)
		self.assertTrue(log.merged_at)
		self.assertTrue(log.merged_by)

	def test_merge_with_child_tables(self):
		lead_a = self._create_lead(first_name="A", email="a@test.com")
		lead_b = self._create_lead(first_name="B", email="b@test.com")

		lead_b.append("products", {"product_name": "Test Product", "rate": 100})
		lead_b.flags.ignore_links = True
		lead_b.save(ignore_permissions=True)

		from crm.api.lead import merge_leads

		merge_leads(lead_a.name, lead_b.name)

		lead_a.reload()
		self.assertEqual(len(lead_a.products), 1)
		self.assertEqual(lead_a.products[0].product_name, "Test Product")

	def test_merge_updates_references(self):
		lead_a = self._create_lead(first_name="A", email="a@test.com")
		lead_b = self._create_lead(first_name="B", email="b@test.com")

		deal = frappe.get_doc(
			{"doctype": "CRM Deal", "lead": lead_b.name}
		)
		deal.flags.ignore_links = True
		deal.insert(ignore_permissions=True)

		from crm.api.lead import merge_leads

		merge_leads(lead_a.name, lead_b.name)

		deal.reload()
		self.assertEqual(deal.lead, lead_a.name)

	def test_merge_updates_dynamic_link_references(self):
		lead_a = self._create_lead(first_name="A", email="a@test.com")
		lead_b = self._create_lead(first_name="B", email="b@test.com")

		comm = frappe.get_doc(
			{
				"doctype": "Communication",
				"subject": "Test email",
				"communication_type": "Communication",
				"status": "Open",
				"sent_or_received": "Sent",
				"reference_doctype": "CRM Lead",
				"reference_name": lead_b.name,
			}
		).insert(ignore_permissions=True)

		todo = frappe.get_doc(
			{
				"doctype": "ToDo",
				"description": "Test task",
				"reference_type": "CRM Lead",
				"reference_name": lead_b.name,
			}
		).insert(ignore_permissions=True)

		from crm.api.lead import merge_leads

		merge_leads(lead_a.name, lead_b.name)

		comm.reload()
		todo.reload()

		self.assertEqual(comm.reference_name, lead_a.name)
		self.assertEqual(todo.reference_name, lead_a.name)

	def test_merge_cannot_merge_already_merged(self):
		lead_a = self._create_lead(first_name="A", email="a@test.com")
		lead_b = self._create_lead(first_name="B", email="b@test.com")

		from crm.api.lead import merge_leads

		merge_leads(lead_a.name, lead_b.name)

		lead_c = self._create_lead(first_name="C", email="c@test.com")
		with self.assertRaises(frappe.ValidationError):
			merge_leads(lead_c.name, lead_b.name)

	def test_split_lead(self):
		lead_a = self._create_lead(
			first_name="Target",
			email="target@test.com",
			mobile_no="+111",
			status="New",
		)
		lead_b = self._create_lead(
			first_name="Source",
			email="source@test.com",
			mobile_no="",
			status="Contacted",
		)

		from crm.api.lead import merge_leads, split_lead

		result = merge_leads(lead_a.name, lead_b.name)

		lead_a.reload()
		# source "Contacted" overwrote target "New"
		self.assertEqual(lead_a.status, "Contacted")

		split_lead(result["merge_log"])

		lead_a.reload()
		lead_b.reload()

		# target fields restored to pre-merge snapshot
		self.assertEqual(lead_a.status, "New")
		self.assertEqual(lead_a.mobile_no, "+111")
		self.assertIsNone(lead_b.merged_into)
		self.assertEqual(lead_b.is_duplicate, 0)

	def test_split_merges_twice_fails(self):
		lead_a = self._create_lead(first_name="A", email="a@test.com")
		lead_b = self._create_lead(first_name="B", email="b@test.com")

		from crm.api.lead import merge_leads, split_lead

		result = merge_leads(lead_a.name, lead_b.name)
		split_lead(result["merge_log"])

		with self.assertRaises(frappe.ValidationError):
			split_lead(result["merge_log"])

	def test_get_merge_history(self):
		lead_a = self._create_lead(first_name="A", email="a@test.com")
		lead_b = self._create_lead(first_name="B", email="b@test.com")

		from crm.api.lead import merge_leads, get_merge_history

		merge_leads(lead_a.name, lead_b.name)
		history = get_merge_history(lead_a.name)
		self.assertEqual(len(history), 1)
		self.assertEqual(history[0]["source_document_name"], lead_b.name)

	def test_create_lead_endpoint(self):
		from crm.api.lead import create_lead

		existing = self._create_lead(first_name="Existing", email="dupe@test.com")

		result = create_lead(
			json.dumps({"first_name": "New", "email": "dupe@test.com"})
		)
		self.assertEqual(result["duplicate_warning"], True)
		self.assertEqual(len(result["possible_duplicates"]), 1)
		self.assertEqual(result["possible_duplicates"][0]["name"], existing.name)
