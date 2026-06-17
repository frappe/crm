"""Pipeline tests with the network stubbed out."""

import os
import sys
import unittest

from bs4 import BeautifulSoup

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from website_intelligence import pipeline as pipeline_mod  # noqa: E402
from website_intelligence.crawler import extract_content  # noqa: E402
from website_intelligence.models import CrawledPage, EnrichmentResult  # noqa: E402
from website_intelligence.pipeline import (  # noqa: E402
    WebsiteIntelligencePipeline, PROGRESS_STEPS, _normalize_website,
)
from website_intelligence.tests import fixtures  # noqa: E402


# The CRM field mapper (crm.api.website_intelligence.FIELD_MAP) relies on this
# schema being identical for every site. If extractors change the shape, these
# assertions fail loudly instead of the mapper silently reading missing keys.
EXPECTED_TOP_KEYS = {
    "company_name", "description", "logo", "industry", "industry_confidence",
    "employees", "emails", "phones", "addresses", "social_profiles",
    "technologies", "contacts", "signals", "_meta",
}
EXPECTED_FLAT_KEYS = {
    "company_name", "description", "logo", "industry", "industry_confidence",
    "employees", "social_profiles",
}
SCALAR_SUBKEYS = {"value", "source", "method"}
SIGNAL_KEYS = {"hiring", "funding", "ai", "matched_snippets"}


def _page(url, html):
    soup = BeautifulSoup(html, "html.parser")
    content = extract_content(BeautifulSoup(html, "html.parser"))
    return CrawledPage(url=url, status_code=200, html=html,
                       text=content["text"], title=content["title"],
                       headings=content["headings"]), soup


class NormalizeTest(unittest.TestCase):
    def test_adds_scheme(self):
        self.assertEqual(_normalize_website("frappe.io"), "https://frappe.io")

    def test_rejects_empty(self):
        with self.assertRaises(ValueError):
            _normalize_website("")

    def test_rejects_bad_scheme(self):
        with self.assertRaises(ValueError):
            _normalize_website("ftp://x.com")


class PipelineTest(unittest.TestCase):
    def setUp(self):
        self._orig = pipeline_mod.discover_relevant_pages
        fake_pages = [
            _page("https://acme.example", fixtures.HOMEPAGE),
            _page("https://acme.example/about", fixtures.ABOUT),
            _page("https://acme.example/contact", fixtures.CONTACT),
        ]
        pipeline_mod.discover_relevant_pages = (
            lambda *a, **k: fake_pages
        )
        # Keep the Wikipedia lookup off the network in tests.
        self._orig_wiki = pipeline_mod.wikipedia.fetch_company_description
        pipeline_mod.wikipedia.fetch_company_description = lambda *a, **k: ("", "")

    def tearDown(self):
        pipeline_mod.discover_relevant_pages = self._orig
        pipeline_mod.wikipedia.fetch_company_description = self._orig_wiki

    def test_full_result_schema_is_explainable(self):
        steps = []
        result = WebsiteIntelligencePipeline(
            "https://acme.example",
            progress=lambda i, m: steps.append((i, m)),
        ).run()
        out = result.to_dict()

        # Canonical keys present.
        for key in ("company_name", "description", "industry", "emails", "phones",
                    "addresses", "social_profiles", "technologies", "contacts",
                    "signals"):
            self.assertIn(key, out)

        # Scalar fields are explainable.
        self.assertEqual(out["company_name"]["value"], "Acme Analytics Inc.")
        self.assertTrue(out["company_name"]["source"])
        self.assertTrue(out["company_name"]["method"])

        # Every list item carries a source.
        for item in out["emails"] + out["phones"] + out["technologies"] + out["contacts"]:
            self.assertTrue(item["source"], f"missing source: {item}")
            self.assertTrue(item["method"], f"missing method: {item}")

        # Signals fired.
        self.assertTrue(out["signals"]["hiring"])
        self.assertTrue(out["signals"]["ai"])

        # Progress emitted all 9 steps in order, ending at "Completed".
        emitted_indices = [i for i, _ in steps]
        self.assertEqual(emitted_indices[-1], len(PROGRESS_STEPS) - 1)
        self.assertEqual(steps[-1][1], "Completed")

    def test_flat_view(self):
        result = WebsiteIntelligencePipeline("https://acme.example").run()
        flat = result.flat()
        self.assertEqual(flat["company_name"], "Acme Analytics Inc.")
        self.assertIsInstance(flat["social_profiles"], dict)


class GracefulFailureTest(unittest.TestCase):
    def test_all_pages_failed_returns_empty_without_raising(self):
        orig = pipeline_mod.discover_relevant_pages
        broken = [CrawledPage(url="https://x.example", status_code=0,
                              error="timeout after 10s")]
        pipeline_mod.discover_relevant_pages = lambda *a, **k: [(broken[0], None)]
        try:
            result = WebsiteIntelligencePipeline("https://x.example").run()
            out = result.to_dict()
            self.assertEqual(out["company_name"]["value"], "")
            self.assertTrue(out["_meta"]["errors"])
        finally:
            pipeline_mod.discover_relevant_pages = orig


class SchemaStabilityTest(unittest.TestCase):
    """The result schema must be identical regardless of what a site exposes —
    this is the contract the CRM field mapper depends on."""

    def _assert_invariants(self, out, flat):
        self.assertEqual(set(out), EXPECTED_TOP_KEYS)
        self.assertEqual(set(flat), EXPECTED_FLAT_KEYS)
        for key in ("company_name", "description", "logo", "industry", "employees"):
            self.assertEqual(set(out[key]), SCALAR_SUBKEYS)
        self.assertEqual(set(out["signals"]), SIGNAL_KEYS)

    def test_empty_result_has_full_schema(self):
        # A bare result (e.g. a site that failed to crawl) still exposes every key.
        result = EnrichmentResult()
        self._assert_invariants(result.to_dict(), result.flat())

    def test_populated_result_has_same_schema(self):
        orig = pipeline_mod.discover_relevant_pages
        orig_wiki = pipeline_mod.wikipedia.fetch_company_description
        pipeline_mod.discover_relevant_pages = lambda *a, **k: [
            _page("https://acme.example", fixtures.HOMEPAGE),
            _page("https://acme.example/about", fixtures.ABOUT),
            _page("https://acme.example/contact", fixtures.CONTACT),
        ]
        pipeline_mod.wikipedia.fetch_company_description = lambda *a, **k: ("", "")
        try:
            result = WebsiteIntelligencePipeline("https://acme.example").run()
        finally:
            pipeline_mod.discover_relevant_pages = orig
            pipeline_mod.wikipedia.fetch_company_description = orig_wiki
        out = result.to_dict()
        self._assert_invariants(out, result.flat())
        # List item shapes the mapper / storage rely on.
        for e in out["emails"]:
            self.assertEqual(set(e), {"value", "source", "method"})
        for p in out["phones"]:
            self.assertEqual(set(p), {"value", "raw", "source", "method"})


if __name__ == "__main__":
    unittest.main(verbosity=2)
