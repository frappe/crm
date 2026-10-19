import json

import frappe
from frappe.desk.form.assign_to import add as assign_add
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
		lead_b = self._create_lead(first_name="Source", mobile_no="", phone="+333", status="Contacted")

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

		deal = frappe.get_doc({"doctype": "CRM Deal", "lead": lead_b.name})
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

	def test_merge_moves_every_reference(self):
		lead_a = self._create_lead(first_name="A", email="a@test.com")
		lead_b = self._create_lead(first_name="B", email="b@test.com")
		for i in range(55):
			frappe.get_doc(
				{
					"doctype": "Comment",
					"comment_type": "Comment",
					"reference_doctype": "CRM Lead",
					"reference_name": lead_b.name,
					"content": f"Comment {i}",
				}
			).insert(ignore_permissions=True)

		from crm.api.lead import merge_leads

		merge_leads(lead_a.name, lead_b.name)

		comments = {"reference_doctype": "CRM Lead", "comment_type": "Comment"}
		self.assertEqual(frappe.db.count("Comment", {**comments, "reference_name": lead_b.name}), 0)
		self.assertEqual(frappe.db.count("Comment", {**comments, "reference_name": lead_a.name}), 55)

	def test_merge_and_split_move_attachments(self):
		lead_a = self._create_lead(first_name="A", email="a@test.com")
		lead_b = self._create_lead(first_name="B", email="b@test.com")
		file = frappe.get_doc(
			{
				"doctype": "File",
				"file_url": "https://example.com/brochure.pdf",
				"attached_to_doctype": "CRM Lead",
				"attached_to_name": lead_b.name,
			}
		).insert(ignore_permissions=True)

		from crm.api.lead import merge_leads, split_lead

		result = merge_leads(lead_a.name, lead_b.name)
		self.assertEqual(frappe.db.get_value("File", file.name, "attached_to_name"), lead_a.name)

		split_lead(result["merge_log"])
		self.assertEqual(frappe.db.get_value("File", file.name, "attached_to_name"), lead_b.name)

	def test_merge_and_split_update_assignees(self):
		lead_a = self._create_lead(first_name="A", email="a@test.com")
		lead_b = self._create_lead(first_name="B", email="b@test.com")
		assign_add({"assign_to": ["Administrator"], "doctype": "CRM Lead", "name": lead_b.name})

		from crm.api.lead import merge_leads, split_lead

		result = merge_leads(lead_a.name, lead_b.name)
		self.assertEqual(
			json.loads(frappe.db.get_value("CRM Lead", lead_a.name, "_assign")), ["Administrator"]
		)
		self.assertFalse(frappe.db.get_value("CRM Lead", lead_b.name, "_assign"))

		split_lead(result["merge_log"])
		self.assertFalse(frappe.db.get_value("CRM Lead", lead_a.name, "_assign"))
		self.assertEqual(
			json.loads(frappe.db.get_value("CRM Lead", lead_b.name, "_assign")), ["Administrator"]
		)

	def test_merge_cannot_merge_already_merged(self):
		lead_a = self._create_lead(first_name="A", email="a@test.com")
		lead_b = self._create_lead(first_name="B", email="b@test.com")

		from crm.api.lead import merge_leads

		merge_leads(lead_a.name, lead_b.name)

		lead_c = self._create_lead(first_name="C", email="c@test.com")
		with self.assertRaises(frappe.ValidationError):
			merge_leads(lead_c.name, lead_b.name)

	def test_copying_a_merged_lead_drops_the_merge_fields(self):
		lead_a = self._create_lead(first_name="A", email="copy-a@test.com")
		lead_b = self._create_lead(first_name="B", email="copy-b@test.com")

		from crm.api.lead import merge_leads

		merge_leads(lead_a.name, lead_b.name)
		# Like Duplicate in the desk, which leaves no_copy fields out
		copy = frappe.copy_doc(frappe.get_doc("CRM Lead", lead_b.name), ignore_no_copy=False)

		self.assertFalse(copy.merged_into)
		self.assertFalse(copy.is_duplicate)

	def test_a_merged_source_can_be_deleted(self):
		lead_a = self._create_lead(first_name="A", email="delete-a@test.com")
		lead_b = self._create_lead(first_name="B", email="delete-b@test.com")

		from crm.api.lead import merge_leads

		merge_leads(lead_a.name, lead_b.name)
		frappe.delete_doc("CRM Lead", lead_b.name)

		self.assertFalse(frappe.db.exists("CRM Lead", lead_b.name))

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

	def test_split_moves_references_back(self):
		lead_a = self._create_lead(first_name="A", email="a@test.com")
		lead_b = self._create_lead(first_name="B", email="b@test.com")

		deal = frappe.get_doc({"doctype": "CRM Deal", "lead": lead_b.name})
		deal.flags.ignore_links = True
		deal.insert(ignore_permissions=True)
		todo = frappe.get_doc(
			{
				"doctype": "ToDo",
				"description": "Test task",
				"reference_type": "CRM Lead",
				"reference_name": lead_b.name,
			}
		).insert(ignore_permissions=True)

		from crm.api.lead import merge_leads, split_lead

		result = merge_leads(lead_a.name, lead_b.name)
		split_lead(result["merge_log"])

		self.assertEqual(frappe.db.get_value("CRM Deal", deal.name, "lead"), lead_b.name)
		self.assertEqual(frappe.db.get_value("ToDo", todo.name, "reference_name"), lead_b.name)

	def test_split_moves_child_rows_back(self):
		lead_a = self._create_lead(first_name="A", email="a@test.com")
		lead_b = self._create_lead(first_name="B", email="b@test.com")

		lead_b.append("products", {"product_name": "Test Product", "rate": 100})
		lead_b.flags.ignore_links = True
		lead_b.save(ignore_permissions=True)

		from crm.api.lead import merge_leads, split_lead

		result = merge_leads(lead_a.name, lead_b.name)
		split_lead(result["merge_log"])

		lead_a.reload()
		lead_b.reload()
		self.assertEqual(len(lead_a.products), 0)
		self.assertEqual([p.product_name for p in lead_b.products], ["Test Product"])

	def test_split_ignores_tampered_snapshot(self):
		lead_a = self._create_lead(first_name="A", email="a@test.com")
		lead_b = self._create_lead(first_name="B", email="b@test.com")
		other = self._create_lead(first_name="Other", email="other@test.com")
		other.append("products", {"product_name": "Other Product", "rate": 10})
		other.flags.ignore_links = True
		other.save(ignore_permissions=True)

		from crm.api.lead import merge_leads, split_lead

		result = merge_leads(lead_a.name, lead_b.name)
		log = frappe.get_doc("CRM Merge Log", result["merge_log"])
		log.db_set(
			{
				"field_snapshot": json.dumps({"lead_score": 99}),
				"child_table_snapshot": json.dumps({"products": [{"name": other.products[0].name}]}),
				"reference_snapshot": json.dumps(
					[
						{
							"doctype": "CRM Lead",
							"docname": other.name,
							"fieldname": "first_name",
							"old_value": lead_b.name,
						}
					]
				),
			}
		)

		split_lead(log.name)

		other.reload()
		self.assertEqual(other.first_name, "Other")
		self.assertEqual([p.product_name for p in other.products], ["Other Product"])
		self.assertNotEqual(frappe.db.get_value("CRM Lead", lead_a.name, "lead_score"), 99)

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

		from crm.api.lead import get_merge_history, merge_leads

		merge_leads(lead_a.name, lead_b.name)
		history = get_merge_history(lead_a.name)
		self.assertEqual(len(history), 1)
		self.assertEqual(history[0]["source_document_name"], lead_b.name)

	def test_create_lead_endpoint(self):
		from crm.api.lead import create_lead

		existing = self._create_lead(first_name="Existing", email="dupe@test.com")

		result = create_lead(json.dumps({"first_name": "New", "email": "dupe@test.com"}))
		self.assertEqual(result["duplicate_warning"], True)
		self.assertEqual(len(result["possible_duplicates"]), 1)
		self.assertEqual(result["possible_duplicates"][0]["name"], existing.name)
