import json
from contextlib import contextmanager
from unittest.mock import patch

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
from frappe.desk.form.assign_to import add as assign_add
from frappe.permissions import add_permission, update_permission_property
from frappe.tests import IntegrationTestCase


class TestMergeLead(IntegrationTestCase):
	def tearDown(self):
		frappe.set_user("Administrator")
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

	def test_find_duplicates_matches_email_in_any_case(self):
		lead1 = self._create_lead(first_name="Mixed", email="mixed.case@test.com")
		lead2 = self._create_lead(first_name="Upper", email="Mixed.Case@Test.com")

		from crm.api.lead import find_duplicate_leads

		dups = {d["name"]: d for d in find_duplicate_leads(lead2.name)}
		self.assertEqual(dups[lead1.name]["matched_fields"], ["email"])

	def test_find_duplicates_treats_email_wildcards_literally(self):
		lead = self._create_lead(first_name="Under", email="under_score@test.com")
		lookalike = self._create_lead(first_name="Lookalike", email="underxscore@test.com")

		from crm.api.lead import find_duplicate_leads

		self.assertNotIn(lookalike.name, [d["name"] for d in find_duplicate_leads(lead.name)])

	def test_find_duplicates_by_mobile(self):
		lead1 = self._create_lead(first_name="Jane", email="jane@test.com", mobile_no="+999")
		lead2 = self._create_lead(first_name="Janet", mobile_no="+999")

		from crm.api.lead import find_duplicate_leads

		dups = find_duplicate_leads(lead2.name)
		names = [d["name"] for d in dups]
		self.assertIn(lead1.name, names)

	def test_find_duplicates_by_differently_formatted_phone(self):
		lead1 = self._create_lead(first_name="Ravi", mobile_no="+91 98765 43210")
		lead2 = self._create_lead(first_name="Ravi K", phone="+91-98765-43210")

		from crm.api.lead import find_duplicate_leads

		dups = {d["name"]: d for d in find_duplicate_leads(lead2.name)}
		self.assertIn(lead1.name, dups)
		self.assertEqual(dups[lead1.name]["matched_fields"], ["mobile_no"])

	def test_find_duplicates_skips_converted_and_merged_leads(self):
		lead = self._create_lead(first_name="Lead", email="same@test.com")
		converted = self._create_lead(first_name="Converted", email="same@test.com")
		converted.db_set("converted", 1)
		target = self._create_lead(first_name="Target", email="target@test.com")
		merged = self._create_lead(first_name="Merged", email="same@test.com")
		merged.db_set({"is_duplicate": 1, "merged_into": target.name})

		from crm.api.lead import find_duplicate_leads

		self.assertEqual(find_duplicate_leads(lead.name), [])

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

		# existing target values are kept, empty ones are filled from the source
		self.assertEqual(lead_a.first_name, "Target")
		self.assertEqual(lead_a.status, "New")
		self.assertEqual(lead_a.mobile_no, "+111")
		self.assertEqual(lead_a.phone, "+333")

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

	def test_merge_and_split_leave_an_info_comment_on_both_leads(self):
		target = self._create_lead(first_name="Target", email="info-target@test.com")
		source = self._create_lead(first_name="Source", email="info-source@test.com")

		from crm.api.lead import merge_leads, split_lead

		def info_comments(lead):
			return frappe.get_all(
				"Comment",
				{"reference_doctype": "CRM Lead", "reference_name": lead, "comment_type": "Info"},
				pluck="content",
				order_by="creation",
			)

		result = merge_leads(target.name, source.name)
		split_lead(result["merge_log"])

		for lead in (target.name, source.name):
			self.assertEqual(info_comments(lead), ["Source merged into Target", "Source split from Target"])

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

	def test_merge_keeps_status_and_sla_history_per_lead(self):
		target = self._create_lead(first_name="Target", email="status-target@test.com", status="New")
		source = self._create_lead(first_name="Source", email="status-source@test.com", status="New")
		source.status = "Contacted"
		source.save(ignore_permissions=True)
		source.append("rolling_responses", {"response_time": 60, "responded_on": "2026-01-01 10:00:00"})
		source.save(ignore_permissions=True)
		target_open_row = target.status_change_log[-1].name

		def rows(lead, table):
			child = frappe.get_meta("CRM Lead").get_field(table).options
			return frappe.get_all(child, {"parent": lead, "parenttype": "CRM Lead"}, ["*"], order_by="idx")

		source_rows = {t: rows(source.name, t) for t in ("status_change_log", "rolling_responses")}

		from crm.api.lead import merge_leads

		merge_leads(target.name, source.name)
		target.reload()
		target.status = "Contacted"
		target.save(ignore_permissions=True)

		closed = frappe.db.get_value(
			"CRM Status Change Log", target_open_row, ["to", "to_date"], as_dict=True
		)
		self.assertEqual(closed.to, "Contacted")
		self.assertTrue(closed.to_date)
		for table, before in source_rows.items():
			self.assertEqual(rows(source.name, table), before)
		self.assertFalse(rows(target.name, "rolling_responses"))

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
			phone="+333",
			status="Contacted",
		)

		from crm.api.lead import merge_leads, split_lead

		result = merge_leads(lead_a.name, lead_b.name)

		lead_a.reload()
		self.assertEqual(lead_a.status, "New")
		self.assertEqual(lead_a.phone, "+333")

		split_lead(result["merge_log"])

		lead_a.reload()
		lead_b.reload()

		# fields filled by the merge are emptied again
		self.assertFalse(lead_a.phone)
		self.assertEqual(lead_a.status, "New")
		self.assertEqual(lead_a.mobile_no, "+111")
		self.assertIsNone(lead_b.merged_into)
		self.assertEqual(lead_b.is_duplicate, 0)

	def test_split_keeps_values_changed_after_the_merge(self):
		lead_a = self._create_lead(first_name="A", status="New")
		lead_b = self._create_lead(first_name="B", phone="+333", job_title="CTO")
		lead_d = self._create_lead(first_name="D", email="d@test.com")

		from crm.api.lead import merge_leads, split_lead

		first = merge_leads(lead_a.name, lead_b.name)
		merge_leads(lead_a.name, lead_d.name)
		frappe.db.set_value("CRM Lead", lead_a.name, "job_title", "CEO")

		split_lead(first["merge_log"])

		lead_a.reload()
		self.assertFalse(lead_a.phone)
		self.assertEqual(lead_a.job_title, "CEO")
		self.assertEqual(lead_a.email, "d@test.com")

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

	def test_split_only_restores_reference_fields(self):
		lead_a = self._create_lead(first_name="A", email="refcheck-a@test.com")
		lead_b = self._create_lead(first_name="B", email="refcheck-b@test.com")
		other = self._create_lead(first_name="Other", email="refcheck-other@test.com")

		from crm.api.lead import merge_leads, split_lead

		result = merge_leads(lead_a.name, lead_b.name)
		# A plain Data field that happens to hold the target's name is not a reference
		other.db_set("first_name", lead_a.name)
		tampered = {"doctype": "CRM Lead", "docname": other.name, "fieldname": "first_name"}
		log = frappe.get_doc("CRM Merge Log", result["merge_log"])
		refs = [*json.loads(log.reference_snapshot), {**tampered, "old_value": lead_b.name}]
		log.db_set("reference_snapshot", json.dumps(refs))

		split_lead(log.name)

		self.assertEqual(frappe.db.get_value("CRM Lead", other.name, "first_name"), lead_a.name)

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

	def test_read_endpoints_need_lead_access(self):
		lead_a = self._create_lead(first_name="A", email="a@test.com")
		lead_b = self._create_lead(first_name="B", email="a@test.com")

		from crm.api.lead import find_duplicate_leads, get_merge_history, merge_leads

		merge_leads(lead_a.name, lead_b.name)
		frappe.set_user(create_user_without_lead_access())

		with self.assertRaises(frappe.PermissionError):
			find_duplicate_leads(lead_a.name)
		with self.assertRaises(frappe.PermissionError):
			get_merge_history(lead_a.name)

	def test_cannot_merge_converted_leads(self):
		from crm.api.lead import merge_leads

		for converted in ("source", "target"):
			with self.subTest(converted=converted):
				lead_a = self._create_lead(first_name="A", email="a@test.com")
				lead_b = self._create_lead(first_name="B", email="b@test.com")
				(lead_b if converted == "source" else lead_a).db_set("converted", 1)
				with self.assertRaises(frappe.ValidationError):
					merge_leads(lead_a.name, lead_b.name)

	def test_cannot_merge_into_merged_lead(self):
		lead_a = self._create_lead(first_name="A", email="a@test.com")
		lead_b = self._create_lead(first_name="B", email="b@test.com")
		lead_c = self._create_lead(first_name="C", email="c@test.com")

		from crm.api.lead import merge_leads

		merge_leads(lead_a.name, lead_b.name)
		with self.assertRaises(frappe.ValidationError):
			merge_leads(lead_b.name, lead_c.name)

	def test_later_merge_keeps_earlier_merge_log(self):
		lead_a = self._create_lead(first_name="A", email="a@test.com")
		lead_b = self._create_lead(first_name="B", email="b@test.com")
		lead_c = self._create_lead(first_name="C", email="c@test.com")

		from crm.api.lead import merge_leads

		first = merge_leads(lead_a.name, lead_b.name)
		merge_leads(lead_c.name, lead_a.name)

		log = frappe.get_doc("CRM Merge Log", first["merge_log"])
		self.assertEqual((log.source_document_name, log.target_document_name), (lead_b.name, lead_a.name))
		self.assertEqual(frappe.db.get_value("CRM Lead", lead_b.name, "merged_into"), lead_a.name)

	def test_chained_merges_split_newest_first(self):
		lead_a = self._create_lead(first_name="A", email="a@test.com")
		lead_b = self._create_lead(first_name="B", email="b@test.com")
		lead_c = self._create_lead(first_name="C", email="c@test.com")
		todo = frappe.get_doc(
			{
				"doctype": "ToDo",
				"description": "Test task",
				"reference_type": "CRM Lead",
				"reference_name": lead_b.name,
			}
		).insert(ignore_permissions=True)

		from crm.api.lead import merge_leads, split_lead

		first = merge_leads(lead_a.name, lead_b.name)
		second = merge_leads(lead_c.name, lead_a.name)
		self.assertEqual(frappe.db.get_value("ToDo", todo.name, "reference_name"), lead_c.name)

		with self.assertRaises(frappe.ValidationError):
			split_lead(first["merge_log"])

		split_lead(second["merge_log"])
		split_lead(first["merge_log"])
		self.assertEqual(frappe.db.get_value("ToDo", todo.name, "reference_name"), lead_b.name)

	def test_search_mergeable_leads_finds_older_leads(self):
		older = self._create_lead(first_name="Zebulon", email="zebulon@test.com")
		for i in range(55):
			self._create_lead(first_name=f"Newer {i}")

		from crm.api.lead import search_mergeable_leads

		results = search_mergeable_leads(txt="zebulon", limit=1)
		self.assertEqual([r["value"] for r in results], [older.name])

	def test_cannot_split_when_target_is_converted(self):
		target = self._create_lead(first_name="Target", mobile_no="+91 97222 22222")
		source = self._create_lead(first_name="Source", email="source-split@test.com")

		from crm.api.lead import merge_leads, split_lead
		from crm.fcrm.doctype.crm_lead.crm_lead import convert_to_deal

		result = merge_leads(target.name, source.name)
		convert_to_deal(lead=target.name)

		with self.assertRaisesRegex(frappe.ValidationError, "converted"):
			split_lead(result["merge_log"])
		self.assertEqual(frappe.db.get_value("CRM Lead", source.name, "merged_into"), target.name)

	def test_merge_and_split_leave_no_source_owner_on_ownerless_target(self):
		owner = create_lead_owner()
		other = create_user_without_lead_access()
		target = self._create_lead(first_name="Target", email="ownerless@test.com")
		frappe.share.add_docshare(
			"CRM Lead", target.name, other, write=1, flags={"ignore_share_permission": True}
		)
		source = self._create_lead(first_name="Source", email="owned@test.com", lead_owner=owner)
		todo = frappe.db.get_value("ToDo", {"reference_name": source.name, "allocated_to": owner}, "name")
		other_share = {"share_doctype": "CRM Lead", "share_name": target.name, "user": other}

		from crm.api.lead import merge_leads, split_lead

		result = merge_leads(target.name, source.name)
		self.assertEqual(frappe.db.get_value("ToDo", todo, "reference_name"), target.name)
		self.assertTrue(frappe.db.exists("DocShare", other_share))
		self.assertFalse(frappe.db.get_value("CRM Lead", target.name, "lead_owner"))

		split_lead(result["merge_log"])

		self.assertTrue(frappe.db.exists("DocShare", other_share))

		self.assertEqual(frappe.db.get_value("ToDo", todo, "reference_name"), source.name)
		self.assertFalse(
			frappe.db.exists(
				"ToDo",
				{"reference_type": "CRM Lead", "reference_name": target.name, "allocated_to": owner},
			)
		)
		self.assertFalse(
			frappe.db.exists(
				"DocShare", {"share_doctype": "CRM Lead", "share_name": target.name, "user": owner}
			)
		)
		self.assertTrue(
			frappe.db.exists(
				"DocShare", {"share_doctype": "CRM Lead", "share_name": source.name, "user": owner}
			)
		)
		self.assertEqual(frappe.db.get_value("CRM Lead", source.name, "lead_owner"), owner)
		self.assertFalse(frappe.db.get_value("CRM Lead", target.name, "lead_owner"))

	def test_merge_and_split_move_unowned_source_shares(self):
		owner = create_lead_owner()
		other = create_user_without_lead_access()
		target = self._create_lead(first_name="Target", email="owned-target@test.com", lead_owner=owner)
		source = self._create_lead(first_name="Source", email="unowned-source@test.com")
		frappe.share.add_docshare(
			"CRM Lead", source.name, other, write=1, flags={"ignore_share_permission": True}
		)

		from crm.api.lead import merge_leads, split_lead

		result = merge_leads(target.name, source.name)
		self.assertTrue(
			frappe.db.exists(
				"DocShare", {"share_doctype": "CRM Lead", "share_name": target.name, "user": other}
			)
		)

		split_lead(result["merge_log"])
		self.assertTrue(
			frappe.db.exists(
				"DocShare", {"share_doctype": "CRM Lead", "share_name": source.name, "user": other}
			)
		)
		self.assertFalse(
			frappe.db.exists(
				"DocShare", {"share_doctype": "CRM Lead", "share_name": target.name, "user": other}
			)
		)

	def test_split_moves_whatsapp_conversation_back_without_confirmation(self):
		target = self._create_lead(first_name="Target", email="wa-target@test.com")
		source = self._create_lead(first_name="Source", mobile_no="+91 96111 11111")
		profile = frappe.get_doc(
			{"doctype": "WA Profile", "name": frappe.generate_hash(length=10), "phone_number": "919611111111"}
		)
		profile.db_insert()
		message = frappe.get_doc(
			{
				"doctype": "WA Message",
				"name": frappe.generate_hash(length=10),
				"to": profile.name,
				"reference_doctype": "CRM Lead",
				"reference_docname": source.name,
			}
		)
		message.db_insert()

		from crm.api.lead import merge_leads, split_lead

		result = merge_leads(target.name, source.name)
		self.assertEqual(frappe.db.get_value("CRM Lead", target.name, "mobile_no"), "+91 96111 11111")
		self.assertEqual(frappe.db.get_value("WA Message", message.name, "reference_docname"), target.name)

		split_lead(result["merge_log"])

		self.assertFalse(frappe.db.get_value("CRM Lead", target.name, "mobile_no"))
		self.assertEqual(frappe.db.get_value("WA Message", message.name, "reference_docname"), source.name)

	def test_patch_syncs_is_duplicate_with_merged_into(self):
		target = self._create_lead(first_name="Target")
		merged = self._create_lead(first_name="Merged")
		stray = self._create_lead(first_name="Stray")
		plain = self._create_lead(first_name="Plain")
		merged.db_set("merged_into", target.name, update_modified=False)
		stray.db_set("is_duplicate", 1, update_modified=False)
		modified = frappe.db.get_value("CRM Lead", merged.name, "modified")

		from crm.patches.v1_0.set_is_duplicate_for_merged_leads import execute

		execute()
		execute()

		def values(name):
			return frappe.db.get_value("CRM Lead", name, ["is_duplicate", "merged_into"])

		self.assertEqual(values(merged.name), (1, target.name))
		self.assertEqual(values(stray.name), (0, None))
		self.assertEqual(values(plain.name), (0, None))
		self.assertEqual(values(target.name), (0, None))
		self.assertEqual(frappe.db.get_value("CRM Lead", merged.name, "modified"), modified)

	def test_merge_checks_access_and_self_merge_before_locking(self):
		lead_a = self._create_lead(first_name="A", email="lock-perm-a@test.com")
		lead_b = self._create_lead(first_name="B", email="lock-perm-b@test.com")

		from crm.api.lead import merge_leads

		cases = (
			(create_user_without_lead_access(), (lead_a.name, lead_b.name), frappe.PermissionError),
			("Administrator", (lead_a.name, lead_a.name), frappe.ValidationError),
		)
		for user, args, error in cases:
			with self.subTest(user=user):
				frappe.set_user(user)
				with capture_queries() as queries, self.assertRaises(error):
					merge_leads(*args)
				frappe.set_user("Administrator")
				self.assertFalse([q for q in queries if "for update" in q.lower()])

	def test_convert_sees_a_merge_committed_after_its_snapshot(self):
		target = self._create_lead(first_name="Target", email="snapshot-target@test.com")
		source = self._create_lead(first_name="Source", email="snapshot-source@test.com")
		# The other connection only sees committed rows
		frappe.db.commit()  # nosemgrep
		self.addCleanup(delete_committed_leads, source.name, target.name)

		# A read before the lock, like a non-Administrator's permission check, fixes this
		# transaction's REPEATABLE READ snapshot before the other request commits.
		frappe.db.get_value("CRM Lead", source.name, "merged_into")
		lead = frappe.qb.DocType("CRM Lead")
		commit_from_another_connection(
			frappe.qb.update(lead)
			.set(lead.merged_into, target.name)
			.set(lead.is_duplicate, 1)
			.where(lead.name == source.name)
		)

		from crm.fcrm.doctype.crm_lead.crm_lead import convert_to_deal

		with self.assertRaisesRegex(frappe.ValidationError, "was merged into"):
			convert_to_deal(lead=source.name)

	def test_merge_and_split_lock_both_leads_in_name_order_first(self):
		source = self._create_lead(first_name="Source", email="lock-source@test.com")
		target = self._create_lead(first_name="Target", email="lock-target@test.com")
		self.assertLess(source.name, target.name)

		from crm.api.lead import merge_leads, split_lead

		def lead_queries(call):
			queries = []
			real_sql = frappe.db.sql

			def record(query, *args, **kwargs):
				queries.append(f"{query} {args} {kwargs}")
				return real_sql(query, *args, **kwargs)

			with patch.object(frappe.db, "sql", side_effect=record):
				result = call()
			return result, [q for q in queries if "tabCRM Lead`" in q and "select" in q.lower()]

		for call in (
			lambda: merge_leads(target.name, source.name),
			lambda: split_lead(frappe.db.get_value("CRM Merge Log", {"target_document_name": target.name})),
		):
			_result, reads = lead_queries(call)
			locks = [q for q in reads if "for update" in q.lower()]
			self.assertIn("for update", reads[0].lower())
			self.assertIn(source.name, locks[0])
			self.assertIn(target.name, locks[1])
			for name in (source.name, target.name):
				loads = [q for q in reads if q.lstrip().upper().startswith("SELECT *") and name in q]
				# The load the merged_into/converted checks read must be a locking read
				self.assertIn("for update", loads[0].lower())

	def test_cannot_convert_a_merged_lead(self):
		lead_a = self._create_lead(first_name="A", email="convert-a@test.com")
		lead_b = self._create_lead(first_name="B", email="convert-b@test.com")
		lead_c = self._create_lead(first_name="C", email="convert-c@test.com")

		from crm.api.lead import merge_leads
		from crm.fcrm.doctype.crm_lead.crm_lead import convert_to_deal

		merge_leads(lead_b.name, lead_a.name)
		merge_leads(lead_c.name, lead_b.name)

		for merged in (lead_a, lead_b):
			with self.assertRaisesRegex(frappe.ValidationError, lead_c.name):
				convert_to_deal(lead=merged.name)
			self.assertFalse(frappe.db.get_value("CRM Lead", merged.name, "converted"))
		self.assertFalse(frappe.db.exists("CRM Deal", {"lead": ("in", [lead_a.name, lead_b.name])}))

	def test_cannot_convert_a_lead_marked_duplicate(self):
		lead = self._create_lead(first_name="Dup", email="convert-dup@test.com")
		lead.db_set("is_duplicate", 1)

		from crm.fcrm.doctype.crm_lead.crm_lead import convert_to_deal

		with self.assertRaises(frappe.ValidationError):
			convert_to_deal(lead=lead.name)

	def test_merge_does_not_copy_unique_fields(self):
		target = self._create_lead(first_name="Target", email="unique-target@test.com")
		source = self._create_lead(
			first_name="Source", email="unique-source@test.com", facebook_lead_id="fb-merge-1"
		)

		from crm.api.lead import merge_leads

		merge_leads(target.name, source.name)
		self.assertFalse(frappe.db.get_value("CRM Lead", target.name, "facebook_lead_id"))
		self.assertEqual(frappe.db.get_value("CRM Lead", source.name, "facebook_lead_id"), "fb-merge-1")

	def test_merge_and_split_move_links_the_dynamic_link_cache_has_not_seen(self):
		target = self._create_lead(first_name="Target", email="stale-target@test.com")
		source = self._create_lead(first_name="Source", email="stale-source@test.com")
		communication = frappe.get_doc(
			{
				"doctype": "Communication",
				"communication_type": "Communication",
				"communication_medium": "Email",
				"sent_or_received": "Sent",
				"subject": "Linked by a raw insert",
			}
		).insert(ignore_permissions=True)
		cache_key = "dynamic_link_map::Communication Link::link_doctype"
		frappe.cache.set_value(cache_key, [])
		self.addCleanup(frappe.cache.delete_value, cache_key)
		link = frappe.get_doc(
			{
				"doctype": "Communication Link",
				"name": frappe.generate_hash(length=10),
				"parent": communication.name,
				"parenttype": "Communication",
				"parentfield": "timeline_links",
				"link_doctype": "CRM Lead",
				"link_name": source.name,
			}
		)
		link.db_insert()

		from crm.api.lead import merge_leads, split_lead

		result = merge_leads(target.name, source.name)
		self.assertEqual(frappe.db.get_value("Communication Link", link.name, "link_name"), target.name)

		split_lead(result["merge_log"])
		self.assertEqual(frappe.db.get_value("Communication Link", link.name, "link_name"), source.name)

	def test_merge_and_split_reject_get_requests(self):
		from frappe.handler import is_valid_http_method

		from crm.api.lead import merge_leads, split_lead

		previous_request = getattr(frappe.local, "request", None)
		self.addCleanup(setattr, frappe.local, "request", previous_request)
		for method in (merge_leads, split_lead):
			frappe.local.request = frappe._dict(method="GET")
			with self.assertRaises(frappe.PermissionError):
				is_valid_http_method(method)
			frappe.local.request = frappe._dict(method="POST")
			is_valid_http_method(method)

	def test_search_mergeable_leads_matches_the_whole_assignee_email(self):
		user = make_user("a@example.com", "Sales Manager")
		make_user("aa@example.com", "Sales Manager")
		mine = self._create_lead(first_name="Picker Mine", email="picker-mine@test.com")
		theirs = self._create_lead(first_name="Picker Theirs", email="picker-theirs@test.com")
		mine.db_set("_assign", json.dumps([user]))
		theirs.db_set("_assign", json.dumps(["aa@example.com"]))

		from crm.api.lead import search_mergeable_leads

		frappe.set_user(user)
		values = [r["value"] for r in search_mergeable_leads(txt="Picker")]
		self.assertIn(mine.name, values)
		self.assertNotIn(theirs.name, values)

	def test_search_mergeable_leads_caps_the_limit(self):
		for i in range(60):
			self._create_lead(first_name=f"Capped {i}")

		from crm.api.lead import search_mergeable_leads

		self.assertEqual(len(search_mergeable_leads(txt="Capped", limit=1000)), 50)

	def test_search_mergeable_leads_treats_wildcards_literally(self):
		percent = self._create_lead(first_name="Pct100% Picker")
		self._create_lead(first_name="Pct100x Picker")
		underscore = self._create_lead(first_name="Und_Picker")
		self._create_lead(first_name="UndxPicker")

		from crm.api.lead import search_mergeable_leads

		self.assertEqual([r["value"] for r in search_mergeable_leads(txt="100%")], [percent.name])
		self.assertEqual([r["value"] for r in search_mergeable_leads(txt="Und_")], [underscore.name])

	def test_search_mergeable_leads_skips_converted_leads(self):
		open_lead = self._create_lead(first_name="Pickable Open", email="pickable-open@test.com")
		converted = self._create_lead(first_name="Pickable Converted", email="pickable-converted@test.com")
		converted.db_set("converted", 1)

		from crm.api.lead import search_mergeable_leads

		values = [r["value"] for r in search_mergeable_leads(txt="Pickable")]
		self.assertIn(open_lead.name, values)
		self.assertNotIn(converted.name, values)

	def test_split_keeps_activity_added_to_the_target_after_the_merge(self):
		target = self._create_lead(first_name="Target", email="activity-target@test.com")
		source = self._create_lead(first_name="Source", email="activity-source@test.com")

		def note(lead, title):
			return frappe.get_doc(
				{
					"doctype": "FCRM Note",
					"title": title,
					"reference_doctype": "CRM Lead",
					"reference_docname": lead,
				}
			).insert(ignore_permissions=True)

		def comment(lead, content):
			return frappe.get_doc(
				{
					"doctype": "Comment",
					"comment_type": "Comment",
					"reference_doctype": "CRM Lead",
					"reference_name": lead,
					"content": content,
				}
			).insert(ignore_permissions=True)

		source_note = note(source.name, "Before the merge")
		source_comment = comment(source.name, "Before the merge")

		from crm.api.lead import merge_leads, split_lead

		result = merge_leads(target.name, source.name)
		self.assertEqual(frappe.db.get_value("FCRM Note", source_note.name, "reference_docname"), target.name)
		self.assertEqual(frappe.db.get_value("Comment", source_comment.name, "reference_name"), target.name)
		later_note = note(target.name, "After the merge")
		later_comment = comment(target.name, "After the merge")

		split_lead(result["merge_log"])

		self.assertEqual(frappe.db.get_value("FCRM Note", source_note.name, "reference_docname"), source.name)
		self.assertEqual(frappe.db.get_value("Comment", source_comment.name, "reference_name"), source.name)
		self.assertEqual(frappe.db.get_value("FCRM Note", later_note.name, "reference_docname"), target.name)
		self.assertEqual(frappe.db.get_value("Comment", later_comment.name, "reference_name"), target.name)

	def test_phone_match_on_merged_lead_resolves_to_target(self):
		target = self._create_lead(first_name="Target", mobile_no="+91 98222 22222", phone="+91 98333 33333")
		source = self._create_lead(first_name="Source", mobile_no="+91 98111 11111")

		from crm.api.lead import merge_leads
		from crm.integrations.api import find_by_phone

		merge_leads(target.name, source.name)

		matches = find_by_phone("+91 98111 11111")
		self.assertEqual([(m["doctype"], m["docname"]) for m in matches], [("CRM Lead", target.name)])
		self.assertEqual(matches[0]["title"], "Target")

	def test_chained_merge_resolves_to_last_target(self):
		lead_a = self._create_lead(first_name="A", mobile_no="+91 98444 44444")
		lead_b = self._create_lead(first_name="B", mobile_no="+91 98555 55555")
		lead_c = self._create_lead(first_name="C", mobile_no="+91 98666 66666")

		from crm.api.lead import merge_leads
		from crm.fcrm.doctype.crm_lead.crm_lead import resolve_merged_lead
		from crm.integrations.api import find_by_phone

		merge_leads(lead_b.name, lead_a.name)
		merge_leads(lead_c.name, lead_b.name)

		self.assertEqual(resolve_merged_lead(lead_a.name), lead_c.name)
		self.assertEqual(resolve_merged_lead(lead_c.name), lead_c.name)
		matches = find_by_phone("+91 98444 44444")
		self.assertEqual([m["docname"] for m in matches], [lead_c.name])

	def test_phone_match_on_lead_merged_into_a_missing_lead_returns_that_lead(self):
		source = self._create_lead(first_name="Source", mobile_no="+91 97333 33333")
		source.db_set({"merged_into": "CRM-LEAD-MISSING", "is_duplicate": 1})

		from crm.integrations.api import find_by_phone

		matches = find_by_phone("+91 97333 33333")
		self.assertEqual([(m["doctype"], m["docname"]) for m in matches], [("CRM Lead", source.name)])

	def test_resolve_merged_lead_stops_on_a_cycle(self):
		lead_a = self._create_lead(first_name="A")
		lead_b = self._create_lead(first_name="B")
		lead_a.db_set("merged_into", lead_b.name)
		lead_b.db_set("merged_into", lead_a.name)

		from crm.fcrm.doctype.crm_lead.crm_lead import resolve_merged_lead

		self.assertIn(resolve_merged_lead(lead_a.name), (lead_a.name, lead_b.name))

	def test_phone_match_on_merged_lead_with_converted_target_returns_deal(self):
		target = self._create_lead(first_name="Target", mobile_no="+91 98777 77777")
		source = self._create_lead(first_name="Source", mobile_no="+91 98888 88888")

		from crm.api.lead import merge_leads
		from crm.fcrm.doctype.crm_lead.crm_lead import convert_to_deal
		from crm.integrations.api import find_by_phone

		merge_leads(target.name, source.name)
		deal = convert_to_deal(lead=target.name)

		matches = find_by_phone("+91 98888 88888")
		self.assertEqual([(m["doctype"], m["docname"]) for m in matches], [("CRM Deal", deal)])

	def test_phone_match_on_merged_lead_with_converted_target_and_no_deal(self):
		target = self._create_lead(first_name="Target", mobile_no="+91 98999 99999")
		source = self._create_lead(first_name="Source", mobile_no="+91 97111 11111")

		from crm.api.lead import merge_leads
		from crm.integrations.api import find_by_phone

		merge_leads(target.name, source.name)
		target.db_set("converted", 1)

		matches = find_by_phone("+91 97111 11111")
		self.assertEqual([(m["doctype"], m["docname"]) for m in matches], [("CRM Lead", target.name)])

	def test_merged_source_email_does_not_create_new_lead(self):
		# Regression lock: an incoming email from a sender that only a merged source lead
		# has already matches that lead and creates nothing. It guards existing behaviour,
		# so it passes without a red phase.
		target = self._create_lead(first_name="Target", email="target-mail@test.com")
		source = self._create_lead(first_name="Source", email="source-mail@test.com")

		from crm.api.lead import merge_leads

		merge_leads(target.name, source.name)

		email_account = frappe.get_doc(
			{
				"doctype": "Email Account",
				"email_account_name": "Test Merge Incoming",
				"email_id": "test-merge-incoming@example.com",
				"enable_incoming": 1,
				"create_lead_from_incoming_email": 1,
			}
		)
		email_account.flags.ignore_mandatory = True
		email_account.flags.ignore_validate = True
		email_account.insert(ignore_permissions=True)

		leads_before = frappe.db.count("CRM Lead")
		frappe.get_doc(
			{
				"doctype": "Communication",
				"communication_type": "Communication",
				"communication_medium": "Email",
				"sent_or_received": "Received",
				"subject": "Hello again",
				"sender": "source-mail@test.com",
				"email_account": email_account.name,
			}
		).insert(ignore_permissions=True)

		self.assertEqual(frappe.db.count("CRM Lead"), leads_before)


MERGE_TEST_FIELDS = ("merge_test_note", "merge_test_secret")
MERGE_TEST_REP = "merge-rep@example.com"
MERGE_TEST_MANAGER = "merge-manager@example.com"


class TestMergeLeadCustomField(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		create_custom_fields(
			{
				"CRM Lead": [
					{
						"fieldname": "merge_test_note",
						"fieldtype": "Data",
						"label": "Merge Test Note",
						"insert_after": "source",
					},
					{
						"fieldname": "merge_test_secret",
						"fieldtype": "Data",
						"label": "Merge Test Secret",
						"insert_after": "source",
						"permlevel": 1,
					},
				]
			},
			ignore_validate=True,
		)
		level_1 = {"parent": "CRM Lead", "role": "Sales Manager", "permlevel": 1, "if_owner": 0}
		cls.added_level_1_perm = not frappe.db.exists("Custom DocPerm", level_1)
		if cls.added_level_1_perm:
			add_permission("CRM Lead", "Sales Manager", 1)
		update_permission_property("CRM Lead", "Sales Manager", 1, "write", 1)
		make_user(MERGE_TEST_REP, "Sales User")
		make_user(MERGE_TEST_MANAGER, "Sales Manager")
		frappe.clear_cache(doctype="CRM Lead")
		# Adding custom field columns is DDL, which implicitly commits; commit the users and perms with it
		frappe.db.commit()  # nosemgrep

	@classmethod
	def tearDownClass(cls):
		frappe.set_user("Administrator")
		for fieldname in MERGE_TEST_FIELDS:
			frappe.delete_doc("Custom Field", f"CRM Lead-{fieldname}", ignore_missing=True, force=True)
		frappe.db.drop_columns("CRM Lead", list(MERGE_TEST_FIELDS))
		if cls.added_level_1_perm:
			frappe.db.delete(
				"Custom DocPerm", {"parent": "CRM Lead", "role": "Sales Manager", "permlevel": 1}
			)
		for user in (MERGE_TEST_REP, MERGE_TEST_MANAGER):
			frappe.delete_doc("User", user, ignore_missing=True, force=True)
		frappe.clear_cache(doctype="CRM Lead")
		# Dropping the custom field columns is DDL, which implicitly commits anyway
		frappe.db.commit()  # nosemgrep
		super().tearDownClass()

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def test_permlevel_field_merges_only_for_users_who_can_write_it(self):
		from crm.api.lead import merge_leads

		for user, copied in ((MERGE_TEST_REP, False), (MERGE_TEST_MANAGER, True)):
			target = frappe.get_doc(
				{"doctype": "CRM Lead", "first_name": "Target", "lead_owner": user}
			).insert(ignore_permissions=True)
			source = frappe.get_doc(
				{
					"doctype": "CRM Lead",
					"first_name": "Source",
					"lead_owner": user,
					"merge_test_secret": "hidden",
				}
			).insert(ignore_permissions=True)

			frappe.set_user(user)
			merge_leads(target.name, source.name)
			frappe.set_user("Administrator")

			value = frappe.db.get_value("CRM Lead", target.name, "merge_test_secret")
			self.assertEqual(value == "hidden", copied, user)

	def test_custom_field_merges_into_empty_target_and_restores_on_split(self):
		target = frappe.get_doc({"doctype": "CRM Lead", "first_name": "Target"}).insert(
			ignore_permissions=True
		)
		source = frappe.get_doc(
			{"doctype": "CRM Lead", "first_name": "Source", "merge_test_note": "from source"}
		).insert(ignore_permissions=True)

		from crm.api.lead import merge_leads, split_lead

		result = merge_leads(target.name, source.name)
		self.assertEqual(frappe.db.get_value("CRM Lead", target.name, "merge_test_note"), "from source")

		split_lead(result["merge_log"])
		self.assertFalse(frappe.db.get_value("CRM Lead", target.name, "merge_test_note"))
		self.assertEqual(frappe.db.get_value("CRM Lead", source.name, "merge_test_note"), "from source")


def create_user_without_lead_access():
	email = "lead-noperm@example.com"
	if not frappe.db.exists("User", email):
		frappe.get_doc(
			{"doctype": "User", "email": email, "first_name": "No Lead", "send_welcome_email": 0}
		).insert(ignore_permissions=True)
	return email


@contextmanager
def capture_queries():
	queries = []
	real_sql = frappe.db.sql

	def record(query, *args, **kwargs):
		queries.append(f"{query} {args} {kwargs}")
		return real_sql(query, *args, **kwargs)

	with patch.object(frappe.db, "sql", side_effect=record):
		yield queries


def commit_from_another_connection(query):
	"""Run a write on a second connection and commit it, as a concurrent request would."""
	from frappe.database import get_db

	conf = frappe.conf
	other = get_db(
		socket=conf.db_socket,
		host=conf.db_host,
		port=conf.db_port,
		user=conf.db_user or conf.db_name,
		password=conf.db_password,
		cur_db_name=conf.db_name,
	)
	other.connect()
	try:
		other.sql(query.get_sql())
		other.commit()
	finally:
		other.close()


def delete_committed_leads(*names):
	frappe.db.rollback()
	for name in names:
		frappe.delete_doc("CRM Lead", name, force=True, ignore_permissions=True)
	frappe.db.commit()  # nosemgrep


def create_lead_owner():
	email = "lead-merge-owner@example.com"
	if not frappe.db.exists("User", email):
		frappe.get_doc(
			{"doctype": "User", "email": email, "first_name": "Merge Owner", "send_welcome_email": 0}
		).insert(ignore_permissions=True)
	return email


def make_user(email, role):
	if not frappe.db.exists("User", email):
		user = frappe.get_doc(
			{"doctype": "User", "email": email, "first_name": email.split("@")[0], "send_welcome_email": 0}
		).insert(ignore_permissions=True)
		user.add_roles(role)
	return email
