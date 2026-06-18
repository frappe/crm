# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Pure unit tests for the crawler mechanics (no network, no DB).

Covers URL normalization, the same-site/registrable-domain check, link-priority
ordering (config-driven keywords), the crawlable filter (asset/scheme/skip-pattern
rejection) and ``extract_content`` (title/headings/visible text).
"""

from __future__ import annotations

from unittest import mock

from frappe.tests import UnitTestCase

from crm.domain_enrichment import browser, crawler
from crm.domain_enrichment.crawler import (
	_is_crawlable,
	_link_priority,
	crawl_page,
	extract_content,
	normalize_url,
	registrable_domain,
	same_site,
)
from crm.domain_enrichment.tests import fixtures

# A 2xx page whose body has almost no readable text -> looks JS-rendered.
_EMPTY_HTML = "<html><head><title>Acme</title></head><body><div id='root'></div></body></html>"
# A render that actually contains content (> JS_RENDER_MIN_TEXT chars of text).
_RICH_HTML = (
	"<html><body><main><h1>Acme Analytics</h1><p>"
	+ ("Acme builds real-time analytics software for modern product teams. " * 8)
	+ "</p></main></body></html>"
)

# The default BFS priority keywords used by the engine when Settings has none.
PRIORITY = [
	("about", 1.0),
	("contact", 1.0),
	("team", 1.0),
	("careers", 1.0),
	("company", 1.0),
]
SKIP_PATTERNS = [r"/wp-admin", r"\?replytocom="]


class NormalizeUrlTest(UnitTestCase):
	def test_strips_fragment(self):
		self.assertEqual(normalize_url("https://x.com/about/#team"), "https://x.com/about")

	def test_strips_trailing_slash_on_path(self):
		self.assertEqual(normalize_url("https://x.com/about/"), "https://x.com/about")

	def test_keeps_root_slash(self):
		# A bare root "/" must not be stripped (path length 1).
		self.assertEqual(normalize_url("https://x.com/"), "https://x.com/")


class RegistrableDomainTest(UnitTestCase):
	def test_strips_www_and_port(self):
		self.assertEqual(registrable_domain("www.example.com:443"), "example.com")

	def test_last_two_labels(self):
		self.assertEqual(registrable_domain("blog.shop.example.com"), "example.com")

	def test_single_label(self):
		self.assertEqual(registrable_domain("localhost"), "localhost")


class SameSiteTest(UnitTestCase):
	def test_ignores_www_and_subdomains(self):
		self.assertTrue(same_site("https://www.x.com/a", "x.com"))
		self.assertTrue(same_site("https://blog.x.com/a", "x.com"))

	def test_rejects_other_domain(self):
		self.assertFalse(same_site("https://other.com/a", "x.com"))


class LinkPriorityTest(UnitTestCase):
	def test_priority_pages_rank_before_generic(self):
		about = _link_priority("https://x.com/about", "About", PRIORITY)
		blog = _link_priority("https://x.com/blog/post", "Read the post", PRIORITY)
		self.assertLess(about, blog)

	def test_anchor_text_counts(self):
		# A generic URL with a priority keyword in the anchor still ranks high.
		hit = _link_priority("https://x.com/p/42", "Our team", PRIORITY)
		miss = _link_priority("https://x.com/p/43", "Read more", PRIORITY)
		self.assertLess(hit, miss)

	def test_non_priority_sorts_last(self):
		generic = _link_priority("https://x.com/random", "", PRIORITY)
		self.assertEqual(generic, len(PRIORITY) + 1)


class IsCrawlableTest(UnitTestCase):
	def test_rejects_non_http_schemes(self):
		self.assertFalse(_is_crawlable("mailto:a@b.com", []))
		self.assertFalse(_is_crawlable("tel:+15555550142", []))
		self.assertFalse(_is_crawlable("javascript:void(0)", []))

	def test_rejects_asset_extensions(self):
		self.assertFalse(_is_crawlable("https://x.com/file.pdf", []))
		self.assertFalse(_is_crawlable("https://x.com/logo.png", []))
		self.assertFalse(_is_crawlable("https://x.com/app.js", []))

	def test_allows_normal_page(self):
		self.assertTrue(_is_crawlable("https://x.com/about", []))

	def test_rejects_configured_skip_pattern(self):
		self.assertFalse(_is_crawlable("https://x.com/wp-admin/edit", SKIP_PATTERNS))
		self.assertFalse(_is_crawlable("https://x.com/post?replytocom=5", SKIP_PATTERNS))
		self.assertTrue(_is_crawlable("https://x.com/about", SKIP_PATTERNS))

	def test_malformed_skip_pattern_treated_as_substring(self):
		# An invalid regex must not crash; it falls back to substring match.
		self.assertFalse(_is_crawlable("https://x.com/[bad", ["[bad"]))


class ExtractContentTest(UnitTestCase):
	def test_pulls_title_headings_and_text(self):
		_page, soup = fixtures.make_page("https://acme.example", fixtures.HOMEPAGE)
		content = extract_content(soup)
		self.assertEqual(content["title"], "Acme Analytics | AI powered SaaS")
		self.assertIn("AI powered analytics", content["headings"])
		self.assertIn("hello@acme.example", content["text"])

	def test_strips_script_and_style(self):
		html = (
			"<html><head><style>.x{}</style></head><body><script>var x=1</script><p>Visible</p></body></html>"
		)
		_page, soup = fixtures.make_page("https://x.com", html)
		content = extract_content(soup)
		self.assertIn("Visible", content["text"])
		self.assertNotIn("var x", content["text"])


class JSRenderFallbackTest(UnitTestCase):
	"""crawl_page's Chromium fallback: gated, background-only, adopt-if-richer."""

	def _fetch_empty(self, *_a, **_k):
		return 200, _EMPTY_HTML, ""

	def test_renders_when_enabled_and_page_is_js_empty(self):
		cfg = fixtures.make_config(settings={"render_js": 1})
		with (
			mock.patch.object(crawler, "fetch", self._fetch_empty),
			mock.patch.object(browser, "render", return_value=(200, _RICH_HTML, "")) as render,
		):
			page, soup = crawl_page("https://spa.example", cfg, allow_render=True)
		render.assert_called_once()
		self.assertIn("real-time analytics", page.text)  # adopted the rendered DOM
		self.assertIsNotNone(soup)

	def test_keeps_requests_html_when_render_is_not_richer(self):
		cfg = fixtures.make_config(settings={"render_js": 1})
		with (
			mock.patch.object(crawler, "fetch", self._fetch_empty),
			mock.patch.object(browser, "render", return_value=(200, "<html><body></body></html>", "")),
		):
			page, _soup = crawl_page("https://spa.example", cfg, allow_render=True)
		self.assertNotIn("real-time analytics", page.text)

	def test_no_render_when_allow_render_false(self):
		# Background-only: the sync/default path must never call the browser, even with render_js on.
		cfg = fixtures.make_config(settings={"render_js": 1})
		with (
			mock.patch.object(crawler, "fetch", self._fetch_empty),
			mock.patch.object(browser, "render") as render,
		):
			crawl_page("https://spa.example", cfg, allow_render=False)
		render.assert_not_called()

	def test_no_render_when_setting_off(self):
		cfg = fixtures.make_config(settings={"render_js": 0})
		with (
			mock.patch.object(crawler, "fetch", self._fetch_empty),
			mock.patch.object(browser, "render") as render,
		):
			crawl_page("https://spa.example", cfg, allow_render=True)
		render.assert_not_called()


class BrowserRenderGuardTest(UnitTestCase):
	"""browser.render bails out (no launch) before touching Chromium."""

	def test_ssrf_rejected_before_launch(self):
		cfg = fixtures.make_config(settings={})
		# Internal/link-local IP -> SSRF guard rejects it; chromium is never imported.
		status, html, error = browser.render("http://169.254.169.254/", cfg)
		self.assertEqual(status, 0)
		self.assertEqual(html, "")
		self.assertIn("SSRF", error)
