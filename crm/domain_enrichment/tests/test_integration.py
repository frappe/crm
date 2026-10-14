# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""IntegrationTestCase tests for the Frappe layer (real test DB).

Covers: seeder idempotency, the mapper write-policies against real CRM
Lead/Deal/Organization docs, the single Run writer, API permission/allow-list
enforcement + rate-limit, and the link-time Organization -> Lead/Deal copy.

All tests are network-free: wherever a crawl would happen the pipeline / fetch is
monkeypatched to return a canned EnrichmentResult, so nothing leaves the box.
"""

from __future__ import annotations

from unittest import mock

import frappe
from frappe.tests import IntegrationTestCase

from crm.domain_enrichment import api, config, install, tasks
from crm.domain_enrichment.config import get_config
from crm.domain_enrichment.cross_record import copy_enrichment_from_organization
from crm.domain_enrichment.mapper import FieldChange, apply_to_document
from crm.domain_enrichment.result import EnrichmentResult, Field, SocialProfile
from crm.domain_enrichment.tests import fixtures


def canned_result(website="https://acme.example") -> EnrichmentResult:
	"""A fully-populated EnrichmentResult — no network, deterministic."""
	r = EnrichmentResult(website=website)
	r.company_name = Field("Acme Analytics Inc.", website, "JSON-LD")
	r.description = Field("AI powered analytics SaaS for product teams.", website, "Meta Tag")
	r.logo = Field("https://acme.example/favicon.ico", website, "Favicon")
	r.industry = Field("SaaS", website, "Keyword Classifier")
	r.industry_confidence = 0.8
	r.social_profiles = {
		"linkedin": SocialProfile("https://www.linkedin.com/company/acme", website),
		"twitter": SocialProfile("https://twitter.com/acme", website),
	}
	return r


class SeederIdempotencyTest(IntegrationTestCase):
	def tearDown(self):
		frappe.db.rollback()

	def test_seeder_is_a_no_op_on_second_run(self):
		# The seeder runs on install/migrate, so records already exist. Running it
		# again must not create duplicate Rule / Field Mapping rows.
		install.seed_default_rules_and_mappings()
		rules_before = frappe.db.count("CRM Enrichment Rule")
		mappings_before = frappe.db.count("CRM Enrichment Field Mapping")

		install.seed_default_rules_and_mappings()

		self.assertEqual(frappe.db.count("CRM Enrichment Rule"), rules_before)
		self.assertEqual(frappe.db.count("CRM Enrichment Field Mapping"), mappings_before)
		self.assertGreater(rules_before, 0)
		self.assertGreater(mappings_before, 0)


class MapperWritePolicyTest(IntegrationTestCase):
	def setUp(self):
		self.cfg = get_config()
		self.result = canned_result()

	def tearDown(self):
		frappe.db.rollback()

	def _new_org(self, **kwargs):
		doc = frappe.new_doc("CRM Organization")
		doc.organization_name = kwargs.pop("organization_name", "Mapper Test Org")
		for k, v in kwargs.items():
			doc.set(k, v)
		return doc

	def test_fill_if_empty_fills_only_empty_fields(self):
		org = self._new_org(company_description="")
		apply_to_document(org, self.result, self.cfg)
		self.assertEqual(org.company_description, "AI powered analytics SaaS for product teams.")

	def test_fill_if_empty_never_clobbers_user_data(self):
		org = self._new_org(company_description="Hand-written by sales.")
		apply_to_document(org, self.result, self.cfg)
		self.assertEqual(org.company_description, "Hand-written by sales.")

	def test_create_missing_link_creates_industry(self):
		industry = "Quantum Widgets " + frappe.generate_hash(length=6)
		self.assertFalse(frappe.db.exists("CRM Industry", industry))
		result = canned_result()
		result.industry = Field(industry, "https://x.example", "Keyword Classifier")
		org = self._new_org(industry="")
		apply_to_document(org, result, self.cfg)
		self.assertTrue(frappe.db.exists("CRM Industry", industry))
		self.assertEqual(org.industry, industry)

	def test_create_missing_link_respects_user_create_permission(self):
		# A user without CRM Industry create rights must not be able to auto-create a
		# master from a scraped value: the master is not inserted and the field is
		# skipped (no dangling link), rather than an ignore_permissions escalation.
		industry = "Contraband Industry " + frappe.generate_hash(length=6)
		result = canned_result()
		result.industry = Field(industry, "https://x.example", "Keyword Classifier")
		org = self._new_org(industry="")

		user = _make_minimal_user()
		self.addCleanup(frappe.set_user, "Administrator")
		frappe.set_user(user)
		apply_to_document(org, result, self.cfg)

		self.assertFalse(frappe.db.exists("CRM Industry", industry))
		self.assertFalse(org.industry)


class RunWriterTest(IntegrationTestCase):
	def tearDown(self):
		frappe.db.rollback()

	def test_writes_exactly_one_run_with_summary(self):
		org = frappe.new_doc("CRM Organization")
		org.organization_name = "Run Writer Org " + frappe.generate_hash(length=4)
		org.website = "https://acme.example"
		org.insert()

		before = frappe.db.count("CRM Enrichment Run", {"reference_name": org.name})
		run_name = tasks.write_run(
			"CRM Organization",
			org.name,
			"https://acme.example",
			status="Completed",
			result=canned_result(),
		)
		after = frappe.db.count("CRM Enrichment Run", {"reference_name": org.name})
		self.assertEqual(after - before, 1)

		run = frappe.get_doc("CRM Enrichment Run", run_name)
		self.assertEqual(run.status, "Completed")
		self.assertEqual(run.company_name, "Acme Analytics Inc.")
		self.assertEqual(run.industry, "SaaS")
		self.assertTrue(run.finished_on)
		self.assertIn("Acme Analytics", run.raw_json)


class RunChangeLogTest(IntegrationTestCase):
	"""run_enrichment records each field it changed as a CRM Enrichment Run Change row."""

	def tearDown(self):
		frappe.db.rollback()

	def _new_org(self, **kwargs):
		org = frappe.new_doc("CRM Organization")
		org.organization_name = "Change Log Org " + frappe.generate_hash(length=4)
		org.website = "https://acme.example"
		for k, v in kwargs.items():
			org.set(k, v)
		org.insert()
		return org

	def _enrich(self, org, result):
		with (
			mock.patch.object(tasks, "run_pipeline", return_value=result),
			mock.patch.object(tasks, "capture"),
		):
			tasks.run_enrichment("CRM Organization", org.name, org.website)
		run_name = frappe.db.get_value(
			"CRM Enrichment Run",
			{"reference_doctype": "CRM Organization", "reference_name": org.name},
			"name",
			order_by="creation desc",
		)
		run = frappe.get_doc("CRM Enrichment Run", run_name)
		self.assertEqual(run.status, "Completed")
		return {c.fieldname: c for c in run.changes}

	def test_records_old_and_new_values(self):
		org = self._new_org(company_description="", twitter="https://twitter.com/old")
		changes = self._enrich(org, canned_result())

		description = changes["company_description"]
		self.assertFalse(description.old_value)
		self.assertEqual(description.new_value, "AI powered analytics SaaS for product teams.")
		self.assertFalse(description.created_link_doctype)
		self.assertEqual(changes["linkedin"].new_value, "https://www.linkedin.com/company/acme")
		# Fill-if-empty left the user's twitter alone, so it is not recorded.
		self.assertNotIn("twitter", changes)

	def test_unchanged_field_creates_no_row(self):
		org = self._new_org(linkedin="https://www.linkedin.com/company/acme")
		changes = self._enrich(org, canned_result())
		self.assertNotIn("linkedin", changes)

	def test_write_run_skips_changes_with_equal_values(self):
		from crm.domain_enrichment.mapper import FieldChange

		org = self._new_org()
		run_name = tasks.write_run(
			"CRM Organization",
			org.name,
			org.website,
			status="Completed",
			changes=[
				FieldChange("linkedin", "https://x.example", "https://x.example", "LinkedIn"),
				FieldChange("twitter", None, "https://twitter.com/acme", "X (Twitter)"),
			],
		)
		run = frappe.get_doc("CRM Enrichment Run", run_name)
		self.assertEqual([c.fieldname for c in run.changes], ["twitter"])

	def test_records_created_industry(self):
		industry = "Quantum Widgets " + frappe.generate_hash(length=6)
		result = canned_result()
		result.industry = Field(industry, "https://x.example", "Keyword Classifier")
		org = self._new_org(industry="")
		changes = self._enrich(org, result)

		self.assertTrue(frappe.db.exists("CRM Industry", industry))
		self.assertEqual(changes["industry"].new_value, industry)
		self.assertEqual(changes["industry"].created_link_doctype, "CRM Industry")

	def test_existing_industry_is_not_marked_created(self):
		industry = "Existing Widgets " + frappe.generate_hash(length=6)
		frappe.get_doc({"doctype": "CRM Industry", "industry": industry}).insert()
		result = canned_result()
		result.industry = Field(industry, "https://x.example", "Keyword Classifier")
		org = self._new_org(industry="")
		changes = self._enrich(org, result)

		self.assertEqual(changes["industry"].new_value, industry)
		self.assertFalse(changes["industry"].created_link_doctype)


class ApiPermissionTest(IntegrationTestCase):
	def tearDown(self):
		frappe.db.rollback()
		frappe.set_user("Administrator")

	def test_enrich_throws_on_disallowed_doctype(self):
		from crm.domain_enrichment.api import enrich

		with self.assertRaises(frappe.ValidationError):
			enrich("ToDo", "anything")

	def test_enrich_requires_write_permission(self):
		from crm.domain_enrichment.api import enrich

		org = frappe.new_doc("CRM Organization")
		org.organization_name = "Perm Org " + frappe.generate_hash(length=4)
		org.website = "https://acme.example"
		org.insert()

		# A user with no role on CRM Organization must be blocked by check_permission.
		user = _make_minimal_user()
		frappe.set_user(user)
		with self.assertRaises(frappe.PermissionError):
			enrich("CRM Organization", org.name)

	def test_enrich_routes_are_rate_limited(self):
		# enrich / retry / undo each carry rate_limit(limit=ENRICH_RATE_LIMIT).
		from crm.domain_enrichment import api

		for fn in (api.enrich, api.retry, api.undo):
			self.assertTrue(hasattr(fn, "__wrapped__"), fn.__name__)


class CrossRecordCopyTest(IntegrationTestCase):
	def setUp(self):
		self.org = frappe.new_doc("CRM Organization")
		self.org.organization_name = "Enriched Org " + frappe.generate_hash(length=4)
		self.org.website = "https://acme.example"
		self.org.company_description = "AI powered analytics SaaS."
		self.org.linkedin = "https://www.linkedin.com/company/acme"
		self.org.insert()
		# Mark it enriched via a completed Run (the cleanest "is enriched" signal).
		tasks.write_run(
			"CRM Organization",
			self.org.name,
			self.org.website,
			status="Completed",
			result=canned_result(),
		)

	def tearDown(self):
		frappe.db.rollback()

	def test_copies_empty_fields_from_enriched_org(self):
		deal = frappe.new_doc("CRM Deal")
		deal.organization = self.org.name
		filled = copy_enrichment_from_organization(deal)
		self.assertTrue(filled)
		self.assertEqual(deal.company_description, "AI powered analytics SaaS.")
		self.assertEqual(deal.linkedin, "https://www.linkedin.com/company/acme")

	def test_does_not_clobber_user_set_fields(self):
		deal = frappe.new_doc("CRM Deal")
		deal.organization = self.org.name
		deal.company_description = "User wrote this."
		copy_enrichment_from_organization(deal)
		self.assertEqual(deal.company_description, "User wrote this.")

	def test_non_enriched_org_is_a_noop(self):
		plain = frappe.new_doc("CRM Organization")
		plain.organization_name = "Plain Org " + frappe.generate_hash(length=4)
		plain.website = "https://plain.example"
		plain.insert()

		deal = frappe.new_doc("CRM Deal")
		deal.organization = plain.name
		filled = copy_enrichment_from_organization(deal)
		self.assertEqual(filled, [])
		self.assertFalse(deal.company_description)


class AutoEnrichOnCreateTest(IntegrationTestCase):
	"""The after_insert auto-enrich hook (Lead, Deal, Organization), gated by Settings."""

	def _settings(self, **overrides):
		s = {
			"enabled": 1,
			"auto_enrich": 1,
			"request_timeout": 10,
			"max_pages": 10,
		}
		s.update(overrides)
		return frappe._dict(s)

	def _doc(self, doctype, website="https://acme.example", name="X1"):
		return frappe._dict(doctype=doctype, name=name, website=website)

	def _run(self, doc, settings):
		# auto_enrich_on_create now does a Settings-only gate (config.get_settings), and
		# enqueue_enrichment reads its timeout the same way -- patch both to the fake
		# Settings and assert on frappe.enqueue.
		with (
			mock.patch.object(config, "get_settings", return_value=settings),
			mock.patch.object(tasks, "get_settings", return_value=settings),
			mock.patch.object(tasks.frappe, "enqueue") as enq,
		):
			tasks.auto_enrich_on_create(doc)
		return enq

	def test_enqueues_for_new_lead(self):
		enq = self._run(self._doc("CRM Lead", name="L1"), self._settings())
		enq.assert_called_once()
		kwargs = enq.call_args.kwargs
		self.assertEqual(kwargs["reference_doctype"], "CRM Lead")
		self.assertEqual(kwargs["job_id"], "domain-enrich-CRM Lead-L1")

	def test_enqueues_for_new_deal(self):
		enq = self._run(self._doc("CRM Deal", name="D1"), self._settings())
		enq.assert_called_once()
		kwargs = enq.call_args.kwargs
		self.assertEqual(kwargs["reference_doctype"], "CRM Deal")
		self.assertEqual(kwargs["job_id"], "domain-enrich-CRM Deal-D1")
		self.assertTrue(kwargs["deduplicate"])

	def test_enqueues_for_new_organization(self):
		enq = self._run(self._doc("CRM Organization", name="O1"), self._settings())
		enq.assert_called_once()
		self.assertEqual(enq.call_args.kwargs["reference_doctype"], "CRM Organization")

	def test_skips_when_auto_enrich_off(self):
		enq = self._run(self._doc("CRM Deal"), self._settings(auto_enrich=0))
		enq.assert_not_called()

	def test_skips_when_feature_disabled(self):
		enq = self._run(self._doc("CRM Deal"), self._settings(enabled=0))
		enq.assert_not_called()

	def test_skips_doctype_outside_the_allow_list(self):
		enq = self._run(self._doc("CRM Task"), self._settings())
		enq.assert_not_called()

	def test_skips_without_website(self):
		enq = self._run(self._doc("CRM Deal", website=""), self._settings())
		enq.assert_not_called()


class UndoTest(IntegrationTestCase):
	"""api.undo reverts the newest run that changed fields on the record;
	api.get_status and api.get_enriched_fields report the state around it."""

	def setUp(self):
		# Run as if enrichment were enabled and no job were in flight, whatever the
		# test site's Settings / queue hold.
		enabled = mock.patch.object(api, "_enabled_doctypes", return_value=list(config.ENRICHABLE_DOCTYPES))
		enqueued = mock.patch.object(api, "is_job_enqueued", return_value=False)
		enabled.start()
		self.job_enqueued = enqueued.start()
		self.addCleanup(mock.patch.stopall)

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def _enriched_org(self, **kwargs):
		org = frappe.new_doc("CRM Organization")
		org.organization_name = "Undo Org " + frappe.generate_hash(length=4)
		org.website = "https://acme.example"
		for k, v in kwargs.items():
			org.set(k, v)
		org.insert()
		with (
			mock.patch.object(tasks, "run_pipeline", return_value=canned_result()),
			mock.patch.object(tasks, "capture"),
		):
			tasks.run_enrichment("CRM Organization", org.name, org.website)
		return frappe.get_doc("CRM Organization", org.name)

	def _latest_run(self, org):
		name = frappe.db.get_value(
			"CRM Enrichment Run",
			{"reference_doctype": "CRM Organization", "reference_name": org.name},
			"name",
			order_by="creation desc",
		)
		return frappe.get_doc("CRM Enrichment Run", name)

	def _reenrich(self, org):
		"""Run the canned enrichment again; it finds the values already there."""
		with (
			mock.patch.object(tasks, "run_pipeline", return_value=canned_result()),
			mock.patch.object(tasks, "capture"),
		):
			tasks.run_enrichment("CRM Organization", org.name, org.website)
		return self._latest_run(org)

	def _reenrich_description(self, org, value):
		"""A Completed re-enrich that changed only ``company_description``."""
		old = org.company_description
		org.company_description = value
		org.save()
		tasks.write_run(
			"CRM Organization",
			org.name,
			org.website,
			status="Completed",
			changes=[FieldChange("company_description", old, value, "Description")],
		)
		return self._latest_run(org)

	def test_undo_reverts_changed_fields(self):
		org = self._enriched_org(company_description="", twitter="https://twitter.com/old")
		self.assertEqual(org.linkedin, "https://www.linkedin.com/company/acme")

		out = api.undo("CRM Organization", org.name)

		org.reload()
		self.assertIn("company_description", out["reverted"])
		self.assertIn("linkedin", out["reverted"])
		self.assertFalse(org.company_description)
		self.assertFalse(org.linkedin)
		# Never written by the run, so untouched by the undo.
		self.assertEqual(org.twitter, "https://twitter.com/old")

	def test_undo_skips_field_edited_after_enrichment(self):
		org = self._enriched_org()
		org.linkedin = "https://www.linkedin.com/company/edited-by-user"
		org.save()

		out = api.undo("CRM Organization", org.name)

		org.reload()
		self.assertIn("linkedin", out["skipped"])
		self.assertNotIn("linkedin", out["reverted"])
		self.assertEqual(org.linkedin, "https://www.linkedin.com/company/edited-by-user")
		self.assertFalse(org.company_description)

	def test_undo_restores_non_text_field(self):
		org = frappe.new_doc("CRM Organization")
		org.organization_name = "Undo Revenue Org " + frappe.generate_hash(length=4)
		org.annual_revenue = 9000
		org.insert()
		tasks.write_run(
			"CRM Organization",
			org.name,
			"https://acme.example",
			status="Completed",
			changes=[FieldChange("annual_revenue", 5000, 9000, "Annual Revenue")],
		)

		out = api.undo("CRM Organization", org.name)

		org.reload()
		self.assertEqual(out["reverted"], ["annual_revenue"])
		self.assertEqual(org.annual_revenue, 5000.0)
		self.assertIsInstance(org.annual_revenue, float)

	def test_undo_run_without_changes_throws(self):
		org = frappe.new_doc("CRM Organization")
		org.organization_name = "Undo No Changes Org " + frappe.generate_hash(length=4)
		org.insert()
		run_name = tasks.write_run("CRM Organization", org.name, "https://acme.example", status="Completed")

		with self.assertRaises(frappe.ValidationError):
			api.undo("CRM Organization", org.name)
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc("CRM Enrichment Run", run_name).undo()

	def test_undo_blocked_while_job_is_queued(self):
		org = self._enriched_org()
		self.job_enqueued.return_value = True

		with self.assertRaises(frappe.ValidationError):
			api.undo("CRM Organization", org.name)
		self.job_enqueued.assert_called_with(tasks.enrichment_job_id("CRM Organization", org.name))
		org.reload()
		self.assertEqual(org.linkedin, "https://www.linkedin.com/company/acme")

	def test_undo_requires_write_permission(self):
		org = self._enriched_org()
		frappe.set_user(_make_minimal_user())

		with self.assertRaises(frappe.PermissionError):
			api.undo("CRM Organization", org.name)

	def test_undo_marks_run_reverted(self):
		org = self._enriched_org()
		api.undo("CRM Organization", org.name)

		run = self._latest_run(org)
		self.assertEqual(run.status, "Reverted")
		self.assertEqual(run.undone_by, "Administrator")
		self.assertTrue(run.undone_on)
		# The latest run is no longer undoable.
		self.assertFalse(api.get_status("CRM Organization", org.name)["can_undo"])
		with self.assertRaises(frappe.ValidationError):
			api.undo("CRM Organization", org.name)

	def test_undo_with_every_field_edited_reverts_nothing(self):
		org = self._enriched_org()
		changed = [c.fieldname for c in self._latest_run(org).changes]
		self.assertTrue(changed)
		edited = {fieldname: f"https://edited.example/{fieldname}" for fieldname in changed}
		if "industry" in edited:
			# A Link field: the user's value must be an existing CRM Industry.
			edited["industry"] = "Edited Industry " + frappe.generate_hash(length=6)
			frappe.get_doc({"doctype": "CRM Industry", "industry": edited["industry"]}).insert()
		org.update(edited)
		org.save()

		out = api.undo("CRM Organization", org.name)

		org.reload()
		self.assertEqual(out["reverted"], [])
		self.assertCountEqual(out["skipped"], changed)
		for fieldname, value in edited.items():
			self.assertEqual(org.get(fieldname), value)
		self.assertEqual(self._latest_run(org).status, "Reverted")

	def test_status_follows_enrich_and_undo(self):
		org = frappe.new_doc("CRM Organization")
		org.organization_name = "Status Org " + frappe.generate_hash(length=4)
		org.website = "https://acme.example"
		org.insert()

		status = api.get_status("CRM Organization", org.name)
		self.assertEqual(status["state"], "idle")
		self.assertTrue(status["has_website"])
		self.assertFalse(status["can_undo"])

		self.job_enqueued.return_value = True
		self.assertEqual(api.get_status("CRM Organization", org.name)["state"], "running")
		self.job_enqueued.assert_called_with(tasks.enrichment_job_id("CRM Organization", org.name))
		self.job_enqueued.return_value = False

		with (
			mock.patch.object(tasks, "run_pipeline", return_value=canned_result()),
			mock.patch.object(tasks, "capture"),
		):
			tasks.run_enrichment("CRM Organization", org.name, org.website)
		status = api.get_status("CRM Organization", org.name)
		self.assertEqual(status["state"], "done")
		self.assertTrue(status["can_undo"])

		api.undo("CRM Organization", org.name)
		status = api.get_status("CRM Organization", org.name)
		self.assertEqual(status["state"], "idle")
		self.assertFalse(status["can_undo"])

	def test_status_idle_for_completed_run_without_changes(self):
		# A legacy run from before the change log: Completed, but no Change rows.
		org = frappe.new_doc("CRM Organization")
		org.organization_name = "Legacy Run Org " + frappe.generate_hash(length=4)
		org.website = "https://acme.example"
		org.insert()
		tasks.write_run("CRM Organization", org.name, org.website, status="Completed")

		status = api.get_status("CRM Organization", org.name)
		self.assertEqual(status["state"], "idle")
		self.assertFalse(status["can_undo"])

	def test_status_has_website_false_without_website(self):
		org = frappe.new_doc("CRM Organization")
		org.organization_name = "No Website Org " + frappe.generate_hash(length=4)
		org.insert()

		self.assertFalse(api.get_status("CRM Organization", org.name)["has_website"])

	def test_status_requires_read_permission(self):
		org = self._enriched_org()
		frappe.set_user(_make_minimal_user())

		with self.assertRaises(frappe.PermissionError):
			api.get_status("CRM Organization", org.name)

	def test_enriched_fields_lists_latest_run_changes(self):
		org = self._enriched_org()
		changed = [c.fieldname for c in self._latest_run(org).changes]

		fields = api.get_enriched_fields("CRM Organization", org.name)

		self.assertCountEqual([f["fieldname"] for f in fields], changed)
		linkedin = next(f for f in fields if f["fieldname"] == "linkedin")
		self.assertEqual(linkedin["value"], "https://www.linkedin.com/company/acme")
		self.assertTrue(linkedin["label"])
		self.assertFalse(any(f["edited"] for f in fields))

	def test_enriched_fields_flags_field_edited_after_enrichment(self):
		org = self._enriched_org()
		org.linkedin = "https://www.linkedin.com/company/edited-by-user"
		org.save()

		fields = api.get_enriched_fields("CRM Organization", org.name)

		self.assertEqual([f["fieldname"] for f in fields if f["edited"]], ["linkedin"])

	def test_enriched_fields_skips_unchanged_field(self):
		# The run found the value already there, so it wrote nothing and gets no icon.
		org = self._enriched_org(linkedin="https://www.linkedin.com/company/acme")

		fields = api.get_enriched_fields("CRM Organization", org.name)

		self.assertNotIn("linkedin", [f["fieldname"] for f in fields])

	def test_enriched_fields_casts_value_to_field_type(self):
		org = frappe.new_doc("CRM Organization")
		org.organization_name = "Enriched Revenue Org " + frappe.generate_hash(length=4)
		org.insert()
		tasks.write_run(
			"CRM Organization",
			org.name,
			"https://acme.example",
			status="Completed",
			changes=[FieldChange("annual_revenue", None, 9000, "Annual Revenue")],
		)

		(field,) = api.get_enriched_fields("CRM Organization", org.name)

		self.assertEqual(field["value"], 9000.0)
		self.assertIsInstance(field["value"], float)
		# write_run alone never saved the value onto the record.
		self.assertTrue(field["edited"])

	def test_enriched_fields_flags_always_refresh_mappings(self):
		org = self._enriched_org()
		fieldname = self._latest_run(org).changes[0].fieldname
		cfg = get_config()
		for mapping in cfg.mappings_by_doctype["CRM Organization"]:
			mapping.write_policy = (
				"Always refresh" if mapping.target_fieldname == fieldname else "Fill if empty"
			)

		with mock.patch.object(api, "get_config", return_value=cfg):
			fields = api.get_enriched_fields("CRM Organization", org.name)

		self.assertEqual([f["fieldname"] for f in fields if f["refreshes"]], [fieldname])

	def test_enriched_fields_empty_after_undo(self):
		org = self._enriched_org()
		api.undo("CRM Organization", org.name)

		self.assertEqual(api.get_enriched_fields("CRM Organization", org.name), [])

	def test_reenrich_with_same_values_keeps_fields_and_undo(self):
		org = self._enriched_org()
		first = self._latest_run(org)
		changed = [c.fieldname for c in first.changes]

		second = self._reenrich(org)
		self.assertEqual(second.status, "Completed")
		self.assertFalse(second.changes)

		fields = api.get_enriched_fields("CRM Organization", org.name)
		self.assertCountEqual([f["fieldname"] for f in fields], changed)
		status = api.get_status("CRM Organization", org.name)
		self.assertEqual(status["state"], "done")
		self.assertTrue(status["can_undo"])

		# Undo skips the no-change re-enrich and reverts the first run.
		out = api.undo("CRM Organization", org.name)
		self.assertCountEqual(out["reverted"], changed)
		self.assertEqual(frappe.db.get_value("CRM Enrichment Run", first.name, "status"), "Reverted")
		# The no-change re-enrich only confirmed the reverted values, so it is Reverted too.
		self.assertEqual(frappe.db.get_value("CRM Enrichment Run", second.name, "status"), "Reverted")
		status = api.get_status("CRM Organization", org.name)
		self.assertEqual(status["state"], "idle")
		self.assertFalse(status["can_undo"])

	def test_undo_reenrich_reverts_only_its_field(self):
		org = self._enriched_org()
		first = self._latest_run(org)
		first_description = org.company_description
		self.assertIn("company_description", [c.fieldname for c in first.changes])

		second = self._reenrich_description(org, "Re-enriched description")
		fields = api.get_enriched_fields("CRM Organization", org.name)
		description = next(f for f in fields if f["fieldname"] == "company_description")
		# The newest run's value wins for a field both runs wrote.
		self.assertEqual(description["value"], "Re-enriched description")
		self.assertFalse(description["edited"])

		out = api.undo("CRM Organization", org.name)

		org.reload()
		self.assertEqual(out["reverted"], ["company_description"])
		self.assertEqual(org.company_description, first_description)
		self.assertEqual(org.linkedin, "https://www.linkedin.com/company/acme")
		self.assertEqual(frappe.db.get_value("CRM Enrichment Run", second.name, "status"), "Reverted")

		fields = api.get_enriched_fields("CRM Organization", org.name)
		self.assertCountEqual([f["fieldname"] for f in fields], [c.fieldname for c in first.changes])
		description = next(f for f in fields if f["fieldname"] == "company_description")
		self.assertEqual(description["value"], first_description)
		self.assertFalse(any(f["edited"] for f in fields))
		status = api.get_status("CRM Organization", org.name)
		self.assertEqual(status["state"], "done")
		self.assertTrue(status["can_undo"])

	def test_undo_every_run_returns_to_idle(self):
		org = self._enriched_org()
		self._reenrich_description(org, "Re-enriched description")

		api.undo("CRM Organization", org.name)
		api.undo("CRM Organization", org.name)

		org.reload()
		self.assertFalse(org.company_description)
		self.assertFalse(org.linkedin)
		self.assertEqual(api.get_enriched_fields("CRM Organization", org.name), [])
		status = api.get_status("CRM Organization", org.name)
		self.assertEqual(status["state"], "idle")
		self.assertFalse(status["can_undo"])
		with self.assertRaises(frappe.ValidationError):
			api.undo("CRM Organization", org.name)

	def test_enriched_fields_requires_read_permission(self):
		org = self._enriched_org()
		frappe.set_user(_make_minimal_user())

		with self.assertRaises(frappe.PermissionError):
			api.get_enriched_fields("CRM Organization", org.name)


def _make_minimal_user():
	"""Create (or reuse) a user with no CRM Organization role for permission tests."""
	email = "de-noperm@example.com"
	if not frappe.db.exists("User", email):
		user = frappe.new_doc("User")
		user.email = email
		user.first_name = "No"
		user.last_name = "Perm"
		user.send_welcome_email = 0
		user.insert(ignore_permissions=True)
	return email
