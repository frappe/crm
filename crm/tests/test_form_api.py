# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import json

import frappe
from frappe.tests import IntegrationTestCase

from crm.api import form as F


def make_form(route, document_type="CRM Lead", **kw):
	"""Create a CRM form (native Web Form) and return its name."""
	payload = {"title": kw.pop("title", "Test Form"), "route": route, "document_type": document_type}
	payload.update(kw)
	return F.save_form(name=None, form=payload)["name"]


class TestFormAPI(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		# a CRM-manager-less user, to exercise the permission gate
		if not frappe.db.exists("User", "sales-user@example.com"):
			user = frappe.get_doc(
				{
					"doctype": "User",
					"email": "sales-user@example.com",
					"first_name": "Sales",
					"roles": [{"role": "Sales User"}],
				}
			).insert(ignore_permissions=True)
			user.reload()
			frappe.db.commit()  # nosemgrep
		super().setUpClass()

	@classmethod
	def tearDownClass(cls):
		frappe.db.rollback()
		super().tearDownClass()

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.flags.in_web_form = False
		frappe.form_dict.pop("web_form", None)
		frappe.db.rollback()

	# ---- field picker ----

	def test_get_form_fields_returns_mappable_and_excludes_breaks(self):
		"""The picker returns collectible fields (first_name) and drops
		layout/no-value fields (Section Break) and unsupported types (Link)."""
		fields = F.get_form_fields("CRM Lead")
		names = {f["fieldname"] for f in fields}
		types = {f["fieldtype"] for f in fields}
		self.assertIn("first_name", names)
		self.assertNotIn("Section Break", types)
		self.assertNotIn("Column Break", types)
		# status is a Link — not collectible on a public form
		self.assertNotIn("status", names)

	def test_get_form_fields_rejects_unsupported_doctype(self):
		with self.assertRaises(frappe.ValidationError):
			F.get_form_fields("User")

	# ---- create / read config + seeding ----

	def test_new_lead_form_seeds_default_layout(self):
		"""A brand-new Lead form is seeded with a contact-capture layout and a
		hidden Status field with a default."""
		name = make_form("seed-lead")
		cfg = F.get_form_config(name)

		visible = [
			f["fieldname"] for f in cfg["fields"] if f["fieldtype"] not in ("Section Break", "Column Break")
		]
		self.assertEqual(visible, ["first_name", "email", "last_name", "phone"])
		# section + column break markers are present
		self.assertIn("Section Break", [f["fieldtype"] for f in cfg["fields"]])
		self.assertIn("Column Break", [f["fieldtype"] for f in cfg["fields"]])
		# first_name is mandatory on Lead
		first = next(f for f in cfg["fields"] if f["fieldname"] == "first_name")
		self.assertTrue(first["reqd"])
		# hidden Status seeded with a non-empty default
		hidden = {h["fieldname"]: h for h in cfg["hidden_fields"]}
		self.assertIn("status", hidden)
		self.assertTrue(hidden["status"]["default"])

	def test_new_deal_form_seeds_organization(self):
		name = make_form("seed-deal", document_type="CRM Deal")
		cfg = F.get_form_config(name)
		visible = [
			f["fieldname"] for f in cfg["fields"] if f["fieldtype"] not in ("Section Break", "Column Break")
		]
		self.assertIn("organization_name", visible)
		hidden = {h["fieldname"] for h in cfg["hidden_fields"]}
		self.assertIn("status", hidden)

	def test_save_form_persists_edits(self):
		name = make_form("edit-me")
		F.save_form(
			name=name,
			form={
				"title": "Edited",
				"route": "edit-me",
				"document_type": "CRM Lead",
				"description": "hello",
				"submit_button_label": "Go",
				"fields": [{"fieldname": "first_name", "label": "Name", "fieldtype": "Data", "reqd": 1}],
				"hidden_fields": [],
			},
		)
		cfg = F.get_form_config(name)
		self.assertEqual(cfg["title"], "Edited")
		self.assertEqual(cfg["description"], "hello")
		self.assertEqual(cfg["submit_button_label"], "Go")
		self.assertEqual([f["fieldname"] for f in cfg["fields"]], ["first_name"])

	def test_redirect_url_round_trips(self):
		name = make_form("redir")
		F.save_form(
			name=name,
			form={
				"title": "R",
				"route": "redir",
				"document_type": "CRM Lead",
				"redirect_url": "https://example.com/thanks",
				"fields": [],
				"hidden_fields": [],
			},
		)
		self.assertEqual(F.get_form_config(name)["redirect_url"], "https://example.com/thanks")
		self.assertEqual(frappe.db.get_value("Web Form", name, "success_url"), "https://example.com/thanks")

	# ---- publish guard ----

	def test_publish_blocked_when_hidden_default_missing(self):
		name = make_form("pub-guard")
		with self.assertRaises(frappe.ValidationError):
			F.save_form(
				name=name,
				form={
					"title": "P",
					"route": "pub-guard",
					"document_type": "CRM Lead",
					"published": 1,
					"fields": [{"fieldname": "first_name", "fieldtype": "Data", "reqd": 1}],
					"hidden_fields": [{"fieldname": "status", "fieldtype": "Link", "default": ""}],
				},
			)

	def test_set_published_blocked_when_hidden_default_missing(self):
		name = make_form("setpub-guard")
		# stuff a hidden field with a blank default, still a draft
		F.save_form(
			name=name,
			form={
				"title": "P",
				"route": "setpub-guard",
				"document_type": "CRM Lead",
				"published": 0,
				"fields": [{"fieldname": "first_name", "fieldtype": "Data", "reqd": 1}],
				"hidden_fields": [{"fieldname": "status", "fieldtype": "Link", "default": ""}],
			},
		)
		with self.assertRaises(frappe.ValidationError):
			F.set_published(name, 1)

	# ---- public config ----

	def test_get_form_only_serves_published(self):
		name = make_form("pub-only")
		with self.assertRaises(frappe.DoesNotExistError):
			F.get_form("pub-only")  # draft
		F.set_published(name, 1)
		cfg = F.get_form("pub-only")
		self.assertEqual(cfg["route"], "pub-only")
		self.assertIn("fields", cfg)

	# ---- submission ----

	def test_submit_form_creates_lead_with_source_and_status(self):
		"""A guest submission creates the Lead, stamps Source = Web Form, and
		applies the hidden Status default via the enrichment hook."""
		name = make_form("submit-lead")
		F.set_published(name, 1)

		F.submit_form("submit-lead", {"first_name": "Ada", "email": "wf-test-ada@test.invalid"})

		lead = frappe.get_all(
			"CRM Lead",
			filters={"email": "wf-test-ada@test.invalid"},
			fields=["name", "first_name", "source", "status"],
		)
		self.assertEqual(len(lead), 1)
		self.assertEqual(lead[0]["first_name"], "Ada")
		self.assertEqual(lead[0]["source"], "Web Form")
		self.assertTrue(lead[0]["status"])  # hidden default applied

	def test_submit_form_validates_required(self):
		name = make_form("submit-required")
		F.set_published(name, 1)
		with self.assertRaises(frappe.ValidationError):
			F.submit_form("submit-required", {"email": "no-name@example.com"})  # first_name required

	def test_submit_form_only_accepts_declared_fields(self):
		"""Fields not on the form are ignored (no mass-assignment)."""
		name = make_form("submit-scoped")
		F.set_published(name, 1)
		F.submit_form(
			"submit-scoped",
			json.dumps(
				{"first_name": "Grace", "email": "grace@example.com", "lead_owner": "sales-user@example.com"}
			),
		)
		lead = frappe.get_all(
			"CRM Lead", filters={"email": "grace@example.com"}, fields=["name", "lead_owner"]
		)
		self.assertEqual(len(lead), 1)
		# lead_owner isn't a declared form field, so it must not have been set from input
		self.assertNotEqual(lead[0]["lead_owner"], "sales-user@example.com")

	def test_submit_form_unpublished_raises(self):
		make_form("submit-draft")  # left as draft
		with self.assertRaises(frappe.DoesNotExistError):
			F.submit_form("submit-draft", {"first_name": "X"})

	# ---- draft dry-run ----

	def test_test_submit_validates_but_creates_nothing(self):
		name = make_form("dry-run")
		before = frappe.db.count("CRM Lead")
		res = F.test_submit_form(name, {"first_name": "Dry"})
		self.assertTrue(res["test"])
		self.assertEqual(frappe.db.count("CRM Lead"), before)
		# still enforces required
		with self.assertRaises(frappe.ValidationError):
			F.test_submit_form(name, {})

	# ---- permissions ----

	def test_non_manager_cannot_manage_forms(self):
		frappe.set_user("sales-user@example.com")
		with self.assertRaises(frappe.PermissionError):
			F.list_forms()
		with self.assertRaises(frappe.PermissionError):
			F.save_form(name=None, form={"title": "X", "route": "nope", "document_type": "CRM Lead"})
