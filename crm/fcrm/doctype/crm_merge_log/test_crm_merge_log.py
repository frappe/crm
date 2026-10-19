import frappe
from frappe.tests import IntegrationTestCase


class TestCRMMergeLog(IntegrationTestCase):
	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def _create_lead(self, **kwargs):
		data = {"doctype": "CRM Lead"}
		data.update(kwargs)
		return frappe.get_doc(data).insert(ignore_permissions=True)

	def test_merge_log_creation(self):
		lead_a = self._create_lead(first_name="A", email="a_log@test.com")
		lead_b = self._create_lead(first_name="B", email="b_log@test.com")

		log = frappe.get_doc(
			{
				"doctype": "CRM Merge Log",
				"reference_doctype": "CRM Lead",
				"target_document_name": lead_a.name,
				"source_document_name": lead_b.name,
			}
		)
		log.insert(ignore_permissions=True)

		self.assertTrue(log.merged_at)
		self.assertTrue(log.merged_by)
		self.assertEqual(log.reference_doctype, "CRM Lead")
		self.assertEqual(log.target_document_name, lead_a.name)
		self.assertEqual(log.source_document_name, lead_b.name)

	def test_merge_log_rejects_same_target_source(self):
		lead = self._create_lead(first_name="Same", email="same_log@test.com")

		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(
				{
					"doctype": "CRM Merge Log",
					"reference_doctype": "CRM Lead",
					"target_document_name": lead.name,
					"source_document_name": lead.name,
				}
			).insert(ignore_permissions=True)

	def test_merge_log_requires_target_and_source(self):
		lead = self._create_lead(first_name="Only", email="only_log@test.com")

		for missing in ("target_document_name", "source_document_name"):
			with self.subTest(missing=missing):
				values = {"target_document_name": lead.name, "source_document_name": lead.name, missing: None}
				with self.assertRaises(frappe.MandatoryError):
					frappe.get_doc(
						{"doctype": "CRM Merge Log", "reference_doctype": "CRM Lead", **values}
					).insert(ignore_permissions=True)

	def test_merge_log_cannot_be_renamed(self):
		lead_a = self._create_lead(first_name="A", email="a_rename_log@test.com")
		lead_b = self._create_lead(first_name="B", email="b_rename_log@test.com")
		log = frappe.get_doc(
			{
				"doctype": "CRM Merge Log",
				"reference_doctype": "CRM Lead",
				"target_document_name": lead_a.name,
				"source_document_name": lead_b.name,
			}
		).insert(ignore_permissions=True)

		with self.assertRaises(frappe.ValidationError):
			frappe.rename_doc("CRM Merge Log", log.name, "MRG-RENAMED")

	def test_sales_roles_cannot_access_merge_log(self):
		lead_a = self._create_lead(first_name="A", email="a_ro_log@test.com")
		lead_b = self._create_lead(first_name="B", email="b_ro_log@test.com")
		log = frappe.get_doc(
			{
				"doctype": "CRM Merge Log",
				"reference_doctype": "CRM Lead",
				"target_document_name": lead_a.name,
				"source_document_name": lead_b.name,
			}
		).insert(ignore_permissions=True)

		for role in ("Sales User", "Sales Manager"):
			with self.subTest(role=role):
				frappe.set_user(make_user(f"merge-log-{role.lower().replace(' ', '-')}@example.com", role))
				with self.assertRaises(frappe.PermissionError):
					frappe.get_doc("CRM Merge Log", log.name).check_permission("read")
				frappe.set_user("Administrator")


def make_user(email, role):
	if not frappe.db.exists("User", email):
		user = frappe.get_doc(
			{"doctype": "User", "email": email, "first_name": email.split("@")[0], "send_welcome_email": 0}
		).insert(ignore_permissions=True)
		user.add_roles(role)
	return email
