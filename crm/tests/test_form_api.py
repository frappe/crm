# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase

from crm.api import form as F


def make_form(route, document_type="CRM Lead", **kw):
	"""Create a CRM form (native Web Form) and return its name."""
	payload = {"title": kw.pop("title", "Test Form"), "route": route, "document_type": document_type}
	payload.update(kw)
	return F.save_form(name=None, form=payload)["name"]


class TestFormAPI(IntegrationTestCase):
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

	# ---- submission enrichment ----

	def test_enrichment_stamps_source_and_hidden_default_on_web_form_insert(self):
		"""A Lead created through the web-form path — the framework's accept() sets
		`in_web_form` and puts the form name in form_dict — is stamped
		Source = Web Form and gets its hidden Status default applied by the
		before_insert hook (enrich_form_submission)."""
		name = make_form("enrich-lead")  # seeds a hidden Status field with a default

		frappe.flags.in_web_form = True
		frappe.form_dict["web_form"] = name
		lead = frappe.get_doc(
			{"doctype": "CRM Lead", "first_name": "Ada", "email": "wf-test-ada@test.invalid"}
		).insert(ignore_permissions=True)

		self.assertEqual(lead.source, "Web Form")
		self.assertTrue(lead.status)  # hidden Status default applied

	def test_enrichment_skipped_without_web_form_flag(self):
		"""Outside the web-form path, the hook is a no-op — a normally created Lead
		is not stamped with the Web Form source."""
		lead = frappe.get_doc(
			{"doctype": "CRM Lead", "first_name": "Bob", "email": "wf-test-bob@test.invalid"}
		).insert(ignore_permissions=True)
		self.assertNotEqual(lead.source, "Web Form")

	def test_hidden_defaults_ignored_when_form_targets_other_doctype(self):
		"""A submission referencing a form for a different doctype must not pull in
		that form's hidden defaults — guards against a spoofed `web_form` param."""
		deal_form = make_form("spoof-deal", document_type="CRM Deal")  # seeds Status = Qualification

		frappe.flags.in_web_form = True
		frappe.form_dict["web_form"] = deal_form  # a Deal form, but we insert a Lead
		lead = frappe.get_doc(
			{"doctype": "CRM Lead", "first_name": "Eve", "email": "wf-test-eve@test.invalid"}
		).insert(ignore_permissions=True)

		# "Qualification" is a Deal status; the guard must keep it off the Lead
		self.assertNotEqual(lead.status, "Qualification")

	# ---- field conditional logic ----

	def test_save_form_persists_field_conditional_rules(self):
		"""depends_on / mandatory_depends_on / read_only_depends_on authored per field in
		the builder are stored on the Web Form fields and returned by get_form_config, so
		the public page can honour them (same model as the framework's Web Form)."""
		name = make_form(
			"dep-rules",
			fields=[
				{"fieldname": "organization", "fieldtype": "Data"},
				{"fieldname": "website", "fieldtype": "Data", "depends_on": "eval:doc.organization"},
				{
					"fieldname": "phone",
					"fieldtype": "Data",
					"mandatory_depends_on": 'eval:doc.organization == "Acme"',
				},
				{
					"fieldname": "last_name",
					"fieldtype": "Data",
					"read_only_depends_on": "eval:doc.first_name",
				},
			],
			hidden_fields=[],
		)
		by = {f.fieldname: f for f in frappe.get_doc("Web Form", name).web_form_fields}
		self.assertEqual(by["website"].depends_on, "eval:doc.organization")
		self.assertEqual(by["phone"].mandatory_depends_on, 'eval:doc.organization == "Acme"')
		self.assertEqual(by["last_name"].read_only_depends_on, "eval:doc.first_name")
		self.assertFalse(by["organization"].depends_on)

		cfg = {f["fieldname"]: f for f in F.get_form_config(name)["fields"]}
		self.assertEqual(cfg["website"]["depends_on"], "eval:doc.organization")
		self.assertEqual(cfg["phone"]["mandatory_depends_on"], 'eval:doc.organization == "Acme"')
		self.assertEqual(cfg["last_name"]["read_only_depends_on"], "eval:doc.first_name")

	# ---- layout persistence ----

	def test_save_without_fields_key_preserves_layout(self):
		"""An update that omits `fields` (e.g. a settings-only save) keeps the existing
		layout instead of wiping it."""
		name = make_form("keep-layout")
		before = len(F.get_form_config(name)["fields"])
		self.assertTrue(before)  # seeded layout exists

		F.save_form(name=name, form={"title": "Renamed", "route": "keep-layout", "document_type": "CRM Lead"})

		self.assertEqual(len(F.get_form_config(name)["fields"]), before)

	# ---- field allowlist ----

	def test_save_form_rejects_denied_field(self):
		"""A payload can't map an internal field the picker excludes."""
		name = make_form("denied-field")
		with self.assertRaises(frappe.ValidationError):
			F.save_form(
				name=name,
				form={
					"title": "D",
					"route": "denied-field",
					"document_type": "CRM Lead",
					"fields": [{"fieldname": "converted", "fieldtype": "Check"}],
					"hidden_fields": [],
				},
			)

	def test_save_form_rejects_layout_break_shadowing_a_field(self):
		"""A break skips the catalog check, so it must not name a real field."""
		name = make_form("break-shadow")
		with self.assertRaises(frappe.ValidationError):
			F.save_form(
				name=name,
				form={
					"title": "B",
					"route": "break-shadow",
					"document_type": "CRM Lead",
					"fields": [{"fieldname": "converted", "fieldtype": "Section Break"}],
					"hidden_fields": [],
				},
			)

	def test_save_form_rejects_unknown_hidden_field(self):
		"""Only the system-managed mandatory fields may be hidden fields."""
		name = make_form("hidden-denied")
		with self.assertRaises(frappe.ValidationError):
			F.save_form(
				name=name,
				form={
					"title": "H",
					"route": "hidden-denied",
					"document_type": "CRM Lead",
					"fields": [{"fieldname": "first_name", "fieldtype": "Data"}],
					"hidden_fields": [{"fieldname": "converted", "fieldtype": "Check", "default": "1"}],
				},
			)

	def test_save_form_takes_fieldtype_from_catalog(self):
		"""fieldtype and options come from the doctype, not the payload."""
		name = make_form(
			"spoof-type",
			fields=[{"fieldname": "first_name", "fieldtype": "Attach", "options": "User"}],
			hidden_fields=[],
		)
		stored = frappe.get_doc("Web Form", name).web_form_fields[0]
		self.assertEqual(stored.fieldname, "first_name")
		self.assertEqual(stored.fieldtype, "Data")
		self.assertFalse(stored.options)

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

	# ---- scope ----

	def test_non_crm_web_form_is_out_of_scope(self):
		"""A Web Form from another module that happens to target CRM Lead must not be
		listed, read, published, or deleted through the CRM forms API."""
		other = frappe.get_doc(
			{
				"doctype": "Web Form",
				"title": "Other App Form",
				"route": "other-app-form",
				"doc_type": "CRM Lead",
				"module": "Core",  # not FCRM
				"is_standard": 0,
				"web_form_fields": [{"fieldname": "first_name", "fieldtype": "Data", "label": "First Name"}],
			}
		).insert(ignore_permissions=True)

		self.assertNotIn(other.name, [f["name"] for f in F.list_forms()])
		with self.assertRaises(frappe.ValidationError):
			F.get_form_config(other.name)
		with self.assertRaises(frappe.ValidationError):
			F.set_published(other.name, 1)
		with self.assertRaises(frappe.ValidationError):
			F.delete_form(other.name)

	# ---- public page: Link options must not corrupt the author's session ----

	def test_link_field_options_preserve_authenticated_session(self):
		"""Rendering a Link field's guest-scoped options for a logged-in author's
		preview must leave the author's live session untouched. Regression for the
		preview-logout bug: frappe.set_user() overwrites session.sid (→ username) and
		wipes session.data, so the enumerate-as-Guest path must snapshot and restore
		them — otherwise the corrupted session is persisted under the real sid and the
		author is demoted to Guest on their next request."""
		from unittest.mock import patch

		from crm.www import crm_form

		# a realistic logged-in author session
		frappe.set_user("Administrator")
		frappe.session.sid = "regression_real_sid"
		frappe.session.data = frappe._dict(
			{
				"user": "Administrator",
				"sid": "regression_real_sid",
				"data": frappe._dict({"session_expiry": "06:00:00", "csrf_token": "tok"}),
			}
		)
		before_user, before_sid, before_data = (
			frappe.session.user,
			frappe.session.sid,
			frappe.session.data,
		)

		# force the guest-enumeration branch (guest_can_select True); the actual
		# query is irrelevant here — we're asserting the session dance is clean
		with (
			patch.object(crm_form, "guest_can_select", return_value=True),
			patch("frappe.get_list", return_value=[]),
		):
			crm_form._link_field_options("CRM Industry")

		self.assertEqual(frappe.session.user, before_user)
		self.assertEqual(frappe.session.sid, before_sid)  # not mangled to the username
		self.assertIs(frappe.session.data, before_data)  # nested data object preserved, not wiped
		self.assertEqual(frappe.session.data.data.get("session_expiry"), "06:00:00")

	def test_link_field_options_skip_switch_for_guest(self):
		"""An anonymous visitor is already in the Guest context, so no session switch
		happens — the query runs directly (set_user is never called)."""
		from unittest.mock import patch

		from crm.www import crm_form

		frappe.set_user("Guest")
		with (
			patch.object(crm_form, "guest_can_select", return_value=True),
			patch("frappe.get_list", return_value=[]),
			patch("frappe.set_user") as mock_set_user,
		):
			crm_form._link_field_options("CRM Industry")
			mock_set_user.assert_not_called()

	# ---- permissions ----

	def test_non_manager_cannot_manage_forms(self):
		# a user without CRM-manager roles, to exercise the permission gate — created
		# in-transaction (no commit) so tearDown's rollback cleans it up
		if not frappe.db.exists("User", "sales-user@example.com"):
			frappe.get_doc(
				{
					"doctype": "User",
					"email": "sales-user@example.com",
					"first_name": "Sales",
					"roles": [{"role": "Sales User"}],
				}
			).insert(ignore_permissions=True)
		frappe.set_user("sales-user@example.com")
		with self.assertRaises(frappe.PermissionError):
			F.list_forms()
		with self.assertRaises(frappe.PermissionError):
			F.save_form(name=None, form={"title": "X", "route": "nope", "document_type": "CRM Lead"})
