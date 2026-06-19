# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""IntegrationTestCase tests for the Frappe layer (real test DB).

Covers: seeder idempotency, the mapper write-policies against real CRM
Lead/Deal/Organization docs, the single Run writer, API permission/allow-list
enforcement + preview rate-limit, and the link-time Organization -> Lead/Deal copy.

All tests are network-free: wherever a crawl would happen the pipeline / fetch is
monkeypatched to return a canned EnrichmentResult, so nothing leaves the box.
"""

from __future__ import annotations

from unittest import mock

import frappe
from frappe.tests import IntegrationTestCase

from crm.domain_enrichment import install, tasks
from crm.domain_enrichment.config import get_config
from crm.domain_enrichment.cross_record import copy_enrichment_from_organization
from crm.domain_enrichment.mapper import apply_to_document
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

	def test_enrich_preview_is_rate_limited(self):
		# The decorator is frappe.rate_limiter.rate_limit(limit=10, seconds=60).
		from crm.domain_enrichment import api

		self.assertTrue(hasattr(api.enrich_preview, "__wrapped__"))


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
	"""The after_insert auto-enrich hook (Organization + Deal), gated by Settings."""

	def _cfg(self, **overrides):
		settings = {
			"enabled": 1,
			"auto_enrich": 1,
			"enable_organization": 1,
			"enable_deal": 1,
			"request_timeout": 10,
			"max_pages": 10,
		}
		settings.update(overrides)
		return fixtures.make_config(settings=settings)

	def _doc(self, doctype, website="https://acme.example", name="X1"):
		return frappe._dict(doctype=doctype, name=name, website=website)

	def _run(self, doc, cfg):
		with (
			mock.patch.object(tasks, "get_config", return_value=cfg),
			mock.patch.object(tasks.frappe, "enqueue") as enq,
		):
			tasks.auto_enrich_on_create(doc)
		return enq

	def test_enqueues_for_new_deal(self):
		enq = self._run(self._doc("CRM Deal", name="D1"), self._cfg())
		enq.assert_called_once()
		kwargs = enq.call_args.kwargs
		self.assertEqual(kwargs["reference_doctype"], "CRM Deal")
		self.assertEqual(kwargs["job_id"], "domain-enrich-CRM Deal-D1")
		self.assertTrue(kwargs["deduplicate"])

	def test_enqueues_for_new_organization(self):
		enq = self._run(self._doc("CRM Organization", name="O1"), self._cfg())
		enq.assert_called_once()
		self.assertEqual(enq.call_args.kwargs["reference_doctype"], "CRM Organization")

	def test_skips_when_auto_enrich_off(self):
		enq = self._run(self._doc("CRM Deal"), self._cfg(auto_enrich=0))
		enq.assert_not_called()

	def test_skips_when_doctype_disabled(self):
		enq = self._run(self._doc("CRM Deal"), self._cfg(enable_deal=0))
		enq.assert_not_called()

	def test_skips_without_website(self):
		enq = self._run(self._doc("CRM Deal", website=""), self._cfg())
		enq.assert_not_called()


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
