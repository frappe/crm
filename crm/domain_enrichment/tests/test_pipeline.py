# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Pure, network-free pipeline tests.

The crawl is stubbed (``pipeline.crawl`` patched to return canned offline pages), so
the whole pipeline runs with zero network. Asserts the assembled ``EnrichmentResult``,
the explainable provenance schema (``to_dict``/``flat``) the mapper depends on, and
the progress-step contract.
"""

from __future__ import annotations

from unittest import mock

from frappe.tests import UnitTestCase

from crm.domain_enrichment import pipeline as pipeline_mod
from crm.domain_enrichment.pipeline import PROGRESS_STEPS, _normalize_website
from crm.domain_enrichment.pipeline import run as run_pipeline
from crm.domain_enrichment.result import EnrichmentResult
from crm.domain_enrichment.tests import fixtures

# The schema the CRM field mapper relies on. If extractors change the shape these
# assertions fail loudly instead of the mapper silently reading missing keys.
EXPECTED_TOP_KEYS = {
	"company_name",
	"description",
	"logo",
	"industry",
	"industry_confidence",
	"emails",
	"phones",
	"social_profiles",
	"_meta",
}
EXPECTED_FLAT_KEYS = {
	"company_name",
	"description",
	"logo",
	"industry",
	"industry_confidence",
	"social_profiles",
}
SCALAR_SUBKEYS = {"value", "source", "method"}


def _full_config():
	"""An in-memory config wired with all the rule types the fixtures exercise."""
	return fixtures.make_config(
		settings={"max_pages": 5, "max_depth": 1, "request_timeout": 5},
		rules_by_type={
			"Industry": fixtures.industry_rules(),
			"Social": fixtures.social_rules(),
		},
	)


def _canned_crawl(*_args, **_kwargs):
	"""Return canned (CrawledPage, soup) tuples instead of crawling the network."""
	return [
		fixtures.make_page("https://acme.example", fixtures.HOMEPAGE),
		fixtures.make_page("https://acme.example/about", fixtures.ABOUT),
		fixtures.make_page("https://acme.example/contact", fixtures.CONTACT),
	]


class NormalizeWebsiteTest(UnitTestCase):
	def test_adds_https_scheme(self):
		self.assertEqual(_normalize_website("frappe.io"), "https://frappe.io")

	def test_rejects_empty(self):
		with self.assertRaises(ValueError):
			_normalize_website("")

	def test_rejects_bad_scheme(self):
		with self.assertRaises(ValueError):
			_normalize_website("ftp://x.com")


class PipelineRunTest(UnitTestCase):
	def setUp(self):
		self.cfg = _full_config()

	def test_full_result_is_explainable(self):
		steps = []
		with mock.patch.object(pipeline_mod, "crawl", _canned_crawl):
			result = run_pipeline(
				"https://acme.example",
				cfg=self.cfg,
				progress=lambda i, m: steps.append((i, m)),
			)
		out = result.to_dict()

		self.assertEqual(out["company_name"]["value"], "Acme Analytics Inc.")
		self.assertTrue(out["company_name"]["source"])
		self.assertTrue(out["company_name"]["method"])

		# Every list item carries provenance.
		for item in out["emails"] + out["phones"]:
			self.assertTrue(item["source"], f"missing source: {item}")
			self.assertTrue(item["method"], f"missing method: {item}")

		# Progress emitted, ending at the final step.
		emitted = [i for i, _ in steps]
		self.assertEqual(emitted[-1], len(PROGRESS_STEPS) - 1)

	def test_flat_view(self):
		with mock.patch.object(pipeline_mod, "crawl", _canned_crawl):
			result = run_pipeline("https://acme.example", cfg=self.cfg)
		flat = result.flat()
		self.assertEqual(flat["company_name"], "Acme Analytics Inc.")
		self.assertIsInstance(flat["social_profiles"], dict)

	def test_unreachable_site_returns_empty_without_raising(self):
		from crm.domain_enrichment.result import CrawledPage

		def broken_crawl(*_a, **_k):
			return [(CrawledPage(url="https://x.example", status_code=0, error="timeout after 5s"), None)]

		with mock.patch.object(pipeline_mod, "crawl", broken_crawl):
			result = run_pipeline("https://x.example", cfg=self.cfg)
		out = result.to_dict()
		self.assertEqual(out["company_name"]["value"], "")
		self.assertTrue(out["_meta"]["errors"])
		self.assertTrue(result.notes)  # carries the "couldn't reach" note


class SchemaStabilityTest(UnitTestCase):
	"""The result schema must be identical regardless of what a site exposes."""

	def _assert_invariants(self, out, flat):
		self.assertEqual(set(out), EXPECTED_TOP_KEYS)
		self.assertEqual(set(flat), EXPECTED_FLAT_KEYS)
		for key in ("company_name", "description", "logo", "industry"):
			self.assertEqual(set(out[key]), SCALAR_SUBKEYS)

	def test_empty_result_has_full_schema(self):
		result = EnrichmentResult()
		self._assert_invariants(result.to_dict(), result.flat())

	def test_populated_result_has_same_schema(self):
		with mock.patch.object(pipeline_mod, "crawl", _canned_crawl):
			result = run_pipeline("https://acme.example", cfg=_full_config())
		out = result.to_dict()
		self._assert_invariants(out, result.flat())
		for e in out["emails"]:
			self.assertEqual(set(e), {"value", "source", "method"})
		for p in out["phones"]:
			self.assertEqual(set(p), {"value", "raw", "source", "method"})
