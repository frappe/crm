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

from crm.domain_enrichment import crawler
from crm.domain_enrichment.crawler import (
	_is_crawlable,
	_link_priority,
	extract_content,
	normalize_url,
	registrable_domain,
	same_site,
)
from crm.domain_enrichment.tests import fixtures
from crm.domain_enrichment.tests.fixtures import make_config

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

	def test_deep_subdomains_collapse_to_registrable(self):
		self.assertEqual(registrable_domain("blog.shop.example.com"), "example.com")

	def test_single_label(self):
		self.assertEqual(registrable_domain("localhost"), "localhost")

	def test_bare_ip_returns_itself(self):
		self.assertEqual(registrable_domain("10.0.0.5"), "10.0.0.5")

	def test_multi_label_public_suffix_keeps_registrable_label(self):
		# The bug this guards: a last-two-labels rule returns "co.uk" here, so every
		# *.co.uk site collapses into one same-site bucket. The PSL keeps the SLD.
		self.assertEqual(registrable_domain("acme.co.uk"), "acme.co.uk")
		self.assertEqual(registrable_domain("www.shop.acme.com.au"), "acme.com.au")

	def test_distinct_orgs_under_a_public_suffix_are_distinct(self):
		self.assertNotEqual(registrable_domain("acme.co.uk"), registrable_domain("evil.co.uk"))

	def test_private_hosting_suffix_is_registrable(self):
		# github.io is a PSL *private* suffix: two Pages tenants are different sites.
		self.assertEqual(registrable_domain("acme.github.io"), "acme.github.io")
		self.assertNotEqual(registrable_domain("acme.github.io"), registrable_domain("other.github.io"))


class SameSiteTest(UnitTestCase):
	def test_ignores_www_and_subdomains(self):
		self.assertTrue(same_site("https://www.x.com/a", "x.com"))
		self.assertTrue(same_site("https://blog.x.com/a", "x.com"))

	def test_rejects_unrelated_org_sharing_a_public_suffix(self):
		# Would be a false "same site" under the naive last-two-labels rule.
		self.assertFalse(same_site("https://evil.co.uk/x", "acme.co.uk"))
		self.assertFalse(same_site("https://other.github.io/x", "acme.github.io"))

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


class ParseSitemapTest(UnitTestCase):
	def test_parses_urlset(self):
		kind, locs = crawler._parse_sitemap(fixtures.URLSET_XML)
		self.assertEqual(kind, "urlset")
		self.assertIn("https://acme.example/about", locs)
		self.assertIn("https://acme.example/contact", locs)
		self.assertIn("https://acme.example/blog/post-1", locs)

	def test_parses_sitemapindex(self):
		kind, locs = crawler._parse_sitemap(fixtures.SITEMAP_INDEX_XML)
		self.assertEqual(kind, "sitemapindex")
		self.assertEqual(
			locs,
			["https://acme.example/sitemap-pages.xml", "https://acme.example/sitemap-blog.xml"],
		)

	def test_malformed_xml_returns_none_kind(self):
		kind, locs = crawler._parse_sitemap("<urlset><url><loc>unclosed")
		self.assertIsNone(kind)
		self.assertEqual(locs, [])

	def test_doctype_rejected_before_parsing(self):
		# Must never reach ET.fromstring with a DTD payload.
		kind, locs = crawler._parse_sitemap(fixtures.MALICIOUS_DOCTYPE_XML)
		self.assertIsNone(kind)
		self.assertEqual(locs, [])

	def test_unrelated_root_element_ignored(self):
		kind, locs = crawler._parse_sitemap("<rss><channel></channel></rss>")
		self.assertIsNone(kind)
		self.assertEqual(locs, [])


class DiscoverSitemapUrlsTest(UnitTestCase):
	def setUp(self):
		self.cfg = make_config()

	def test_uses_robots_declared_sitemap(self):
		robots = mock.Mock()
		robots.site_maps.return_value = ["https://acme.example/my-sitemap.xml"]
		responses = {"https://acme.example/my-sitemap.xml": (200, fixtures.URLSET_XML)}
		with mock.patch.object(crawler, "fetch", side_effect=fixtures.fake_fetch(responses)):
			urls = crawler.discover_sitemap_urls("https://acme.example", self.cfg, None, robots)
		self.assertIn("https://acme.example/about", urls)
		self.assertIn("https://acme.example/contact", urls)

	def test_falls_back_to_conventional_path_when_robots_declares_none(self):
		robots = mock.Mock()
		robots.site_maps.return_value = None
		responses = {"https://acme.example/sitemap.xml": (200, fixtures.URLSET_XML)}
		with mock.patch.object(crawler, "fetch", side_effect=fixtures.fake_fetch(responses)):
			urls = crawler.discover_sitemap_urls("https://acme.example", self.cfg, None, robots)
		self.assertIn("https://acme.example/about", urls)

	def test_falls_back_when_robots_is_none(self):
		responses = {"https://acme.example/sitemap.xml": (200, fixtures.URLSET_XML)}
		with mock.patch.object(crawler, "fetch", side_effect=fixtures.fake_fetch(responses)):
			urls = crawler.discover_sitemap_urls("https://acme.example", self.cfg, None, None)
		self.assertIn("https://acme.example/about", urls)

	def test_missing_sitemap_returns_empty_without_raising(self):
		with mock.patch.object(crawler, "fetch", side_effect=fixtures.fake_fetch({})):
			urls = crawler.discover_sitemap_urls("https://acme.example", self.cfg, None, None)
		self.assertEqual(urls, [])

	def test_malformed_xml_returns_empty(self):
		responses = {"https://acme.example/sitemap.xml": (200, "not xml at all")}
		with mock.patch.object(crawler, "fetch", side_effect=fixtures.fake_fetch(responses)):
			urls = crawler.discover_sitemap_urls("https://acme.example", self.cfg, None, None)
		self.assertEqual(urls, [])

	def test_follows_one_level_of_sitemap_index(self):
		responses = {
			"https://acme.example/sitemap.xml": (200, fixtures.SITEMAP_INDEX_XML),
			"https://acme.example/sitemap-pages.xml": (200, fixtures.URLSET_XML),
			"https://acme.example/sitemap-blog.xml": (
				200,
				'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
				"<url><loc>https://acme.example/blog/hello</loc></url></urlset>",
			),
		}
		with mock.patch.object(crawler, "fetch", side_effect=fixtures.fake_fetch(responses)):
			urls = crawler.discover_sitemap_urls("https://acme.example", self.cfg, None, None)
		self.assertIn("https://acme.example/about", urls)
		self.assertIn("https://acme.example/blog/hello", urls)

	def test_rejects_cross_site_sitemap(self):
		# The sitemap FILE lives on a different site than the one we're enriching --
		# must never be fetched, regardless of what its <loc> entries claim. Uses
		# real-style ".com" hosts (not "*.example") so registrable_domain() actually
		# differentiates them -- ".example" isn't in the bundled Public Suffix List,
		# so acme.example/evil.example would collapse to the same registrable domain.
		robots = mock.Mock()
		robots.site_maps.return_value = ["https://evil-corp.com/sitemap.xml"]
		responses = {
			"https://evil-corp.com/sitemap.xml": (
				200,
				'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
				"<url><loc>https://evil-corp.com/about</loc></url></urlset>",
			)
		}
		with mock.patch.object(crawler, "fetch", side_effect=fixtures.fake_fetch(responses)):
			urls = crawler.discover_sitemap_urls("https://acme-corp.com", self.cfg, None, robots)
		self.assertEqual(urls, [])


class CrawlSitemapSeedingTest(UnitTestCase):
	"""End-to-end: crawl() seeded from a robots.txt-declared sitemap.

	Sitemap discovery must be a pure addition on top of the ordinary BFS: it should
	surface a page that isn't linked from the homepage, without displacing the
	homepage as the first crawled result, and it must disappear cleanly (no error)
	when disabled or when the site has no sitemap at all.
	"""

	HOMEPAGE_HTML = '<html><head><title>Acme</title></head><body><a href="/contact">Contact</a></body></html>'
	CONTACT_HTML = "<html><body>Contact us</body></html>"
	HIDDEN_ABOUT_HTML = "<html><head><title>Hidden About</title></head><body><h1>About</h1></body></html>"
	ROBOTS_TXT = "Sitemap: https://acme.example/sitemap.xml"
	SITEMAP_XML = (
		'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
		"<url><loc>https://acme.example/hidden-about</loc></url></urlset>"
	)

	def _responses(self, **overrides):
		base = {
			"https://acme.example": (200, self.HOMEPAGE_HTML),
			"https://acme.example/robots.txt": (200, self.ROBOTS_TXT),
			"https://acme.example/sitemap.xml": (200, self.SITEMAP_XML),
			"https://acme.example/contact": (200, self.CONTACT_HTML),
			"https://acme.example/hidden-about": (200, self.HIDDEN_ABOUT_HTML),
		}
		base.update(overrides)
		return base

	def test_sitemap_only_page_is_crawled_homepage_stays_first(self):
		cfg = make_config(
			settings={"max_pages": 10, "max_depth": 1, "use_sitemap": 1},
			link_priority=PRIORITY,
			skip_patterns=[],
		)
		with mock.patch.object(crawler, "fetch", side_effect=fixtures.fake_fetch(self._responses())):
			results = crawler.crawl("https://acme.example", cfg)
		urls = [page.url for page, _soup in results]
		self.assertEqual(urls[0], "https://acme.example")
		self.assertIn("https://acme.example/hidden-about", urls)
		self.assertIn("https://acme.example/contact", urls)

	def test_use_sitemap_disabled_never_fetches_sitemap(self):
		cfg = make_config(
			settings={"max_pages": 10, "max_depth": 1, "use_sitemap": 0},
			link_priority=PRIORITY,
			skip_patterns=[],
		)
		with mock.patch.object(crawler, "fetch", side_effect=fixtures.fake_fetch(self._responses())):
			results = crawler.crawl("https://acme.example", cfg)
		urls = [page.url for page, _soup in results]
		self.assertEqual(urls[0], "https://acme.example")
		self.assertNotIn("https://acme.example/hidden-about", urls)
		self.assertIn("https://acme.example/contact", urls)

	def test_no_sitemap_falls_through_to_plain_link_following(self):
		# robots.txt exists but declares no sitemap, and /sitemap.xml 404s -- the
		# crawl must proceed exactly as ordinary link-following, no error surfaced.
		responses = self._responses(**{"https://acme.example/robots.txt": (200, "User-agent: *")})
		del responses["https://acme.example/sitemap.xml"]
		cfg = make_config(
			settings={"max_pages": 10, "max_depth": 1, "use_sitemap": 1},
			link_priority=PRIORITY,
			skip_patterns=[],
		)
		with mock.patch.object(crawler, "fetch", side_effect=fixtures.fake_fetch(responses)):
			results = crawler.crawl("https://acme.example", cfg)
		urls = [page.url for page, _soup in results]
		self.assertEqual(urls[0], "https://acme.example")
		self.assertIn("https://acme.example/contact", urls)
		self.assertNotIn("https://acme.example/hidden-about", urls)
		self.assertEqual(len(results), 2)  # homepage + contact only, no crash, no phantom pages
