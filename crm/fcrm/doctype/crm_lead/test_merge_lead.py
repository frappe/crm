import json

import frappe
from frappe.desk.form.assign_to import add as assign_add
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

		from crm.api.lead import merge_leads, resolve_merged_lead
		from crm.integrations.api import find_by_phone

		merge_leads(lead_b.name, lead_a.name)
		merge_leads(lead_c.name, lead_b.name)

		self.assertEqual(resolve_merged_lead(lead_a.name), lead_c.name)
		self.assertEqual(resolve_merged_lead(lead_c.name), lead_c.name)
		matches = find_by_phone("+91 98444 44444")
		self.assertEqual([m["docname"] for m in matches], [lead_c.name])

	def test_resolve_merged_lead_stops_on_a_cycle(self):
		lead_a = self._create_lead(first_name="A")
		lead_b = self._create_lead(first_name="B")
		lead_a.db_set("merged_into", lead_b.name)
		lead_b.db_set("merged_into", lead_a.name)

		from crm.api.lead import resolve_merged_lead

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


def create_user_without_lead_access():
	email = "lead-noperm@example.com"
	if not frappe.db.exists("User", email):
		frappe.get_doc(
			{"doctype": "User", "email": email, "first_name": "No Lead", "send_welcome_email": 0}
		).insert(ignore_permissions=True)
	return email
