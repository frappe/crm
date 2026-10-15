# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Pure unit tests for the crawler mechanics (no network, no DB).

Covers URL normalization, the same-site/registrable-domain check, link-priority
ordering (config-driven keywords), the crawlable filter (asset/scheme/skip-pattern
rejection) and ``extract_content`` (title/headings/visible text).
"""

from __future__ import annotations

from frappe.tests import UnitTestCase

from crm.domain_enrichment.crawler import (
	_is_crawlable,
	_link_priority,
	extract_content,
	normalize_url,
	registrable_domain,
	same_site,
)
from crm.domain_enrichment.tests import fixtures

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
