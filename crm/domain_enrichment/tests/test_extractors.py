# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Pure, network-free unit tests for the config-driven extractors.

The classifiers (industry / social) are exercised with **in-memory Rule objects**
built directly (see ``tests.fixtures``), never the DB — this is the rule-driven
rewrite of the POC's extractor tests. The mechanics (company-name cleaning, favicon
scorer, JSON-LD parse, email/phone extraction, readability diagnosis) are tested
standalone.
"""

from __future__ import annotations

from frappe.tests import UnitTestCase

from crm.domain_enrichment import extractors
from crm.domain_enrichment.result import CrawledPage, Method
from crm.domain_enrichment.tests import fixtures


def _pages(*specs):
	"""specs: (url, html) tuples -> list[CrawledPage], soups_by_url dict."""
	pages, soups = [], {}
	for url, html in specs:
		page, soup = fixtures.make_page(url, html)
		pages.append(page)
		soups[url] = soup
	return pages, soups


# --------------------------------------------------------------------------- #
# Company information (mechanics)
# --------------------------------------------------------------------------- #
class CompanyInfoTest(UnitTestCase):
	def setUp(self):
		self.page, self.soup = fixtures.make_page("https://acme.example", fixtures.HOMEPAGE)

	def test_prefers_json_ld_for_name(self):
		info = extractors.extract_company_info(self.page, self.soup)
		self.assertEqual(info["company_name"].value, "Acme Analytics Inc.")
		self.assertEqual(info["company_name"].method, Method.JSON_LD)
		self.assertEqual(info["company_name"].source, "https://acme.example")

	def test_description_from_json_ld(self):
		info = extractors.extract_company_info(self.page, self.soup)
		self.assertIn("analytics", info["description"].value.lower())

	def test_logo_falls_back_to_favicon_ico(self):
		info = extractors.extract_company_info(self.page, self.soup)
		self.assertEqual(info["logo"].method, Method.FAVICON)
		self.assertEqual(info["logo"].value, "https://acme.example/favicon.ico")

	def test_logo_prefers_declared_apple_touch_icon(self):
		page, soup = fixtures.make_page(
			"https://x.example",
			"<html><head>"
			"<link rel='icon' href='/fav.png' sizes='16x16'>"
			"<link rel='apple-touch-icon' href='/touch.png'>"
			"</head><body></body></html>",
		)
		info = extractors.extract_company_info(page, soup)
		self.assertEqual(info["logo"].value, "https://x.example/touch.png")

	def test_meta_fallback_when_no_json_ld(self):
		page, soup = fixtures.make_page(
			"https://x.example",
			"<html><head><title>Foo</title><meta property='og:site_name' content='Foo Inc'></head><body></body></html>",
		)
		info = extractors.extract_company_info(page, soup)
		self.assertEqual(info["company_name"].value, "Foo Inc")
		self.assertEqual(info["company_name"].method, Method.META_TAG)

	def test_broken_json_ld_does_not_crash(self):
		page, soup = fixtures.make_page("https://b.example", fixtures.BROKEN_JSON_LD)
		info = extractors.extract_company_info(page, soup)
		self.assertEqual(info["company_name"].method, Method.TITLE_TAG)


class CompanyNameCleaningTest(UnitTestCase):
	def test_strips_tagline_after_separator(self):
		self.assertEqual(extractors._clean_company_name("PostHog – dev tools"), "PostHog")

	def test_trims_descriptive_sentence_title(self):
		self.assertEqual(
			extractors._clean_company_name(
				"ITC Ltd has diversified presence in FMCG, Paperboards & Packaging"
			),
			"ITC Ltd",
		)
		self.assertEqual(extractors._clean_company_name("Acme Corp provides cloud security"), "Acme Corp")

	def test_brand_at_end_matches_domain(self):
		self.assertEqual(
			extractors._clean_company_name(
				"Innovative IT & Software Development Services | 8848 Digital",
				"https://8848digital.com/",
			),
			"8848 Digital",
		)

	def test_without_domain_hint_falls_back_to_first_chunk(self):
		self.assertEqual(
			extractors._clean_company_name("Innovative IT & Software Development Services | 8848 Digital"),
			"Innovative IT & Software Development Services",
		)


class JsonLdTest(UnitTestCase):
	def test_parses_graph_blocks(self):
		_page, soup = fixtures.make_page(
			"https://x.com",
			'<html><head><script type="application/ld+json">'
			'{"@graph":[{"@type":"Organization","name":"A"},{"@type":"WebSite"}]}'
			"</script></head><body></body></html>",
		)
		blocks = extractors.parse_json_ld(soup)
		self.assertEqual(len(blocks), 2)
		self.assertEqual(blocks[0]["name"], "A")

	def test_ignores_invalid_json(self):
		_page, soup = fixtures.make_page("https://x.com", fixtures.BROKEN_JSON_LD)
		self.assertEqual(extractors.parse_json_ld(soup), [])


class DescriptionSelectionTest(UnitTestCase):
	def test_prefers_about_over_product_homepage(self):
		pages, soups = _pages(
			(
				"https://shop.example",
				"<html><head><meta property='og:description' content='Shop the latest gadgets.'></head><body></body></html>",
			),
			(
				"https://shop.example/about",
				"<html><head><meta name='description' content='Acme builds developer tools for teams.'></head><body></body></html>",
			),
		)
		desc = extractors.select_description(pages, soups)
		self.assertEqual(desc.value, "Acme builds developer tools for teams.")
		self.assertEqual(desc.source, "https://shop.example/about")

	def test_falls_back_to_homepage(self):
		pages, soups = _pages(
			(
				"https://x.example",
				"<html><head><meta property='og:description' content='We make great software.'></head><body></body></html>",
			),
		)
		desc = extractors.select_description(pages, soups)
		self.assertEqual(desc.value, "We make great software.")

	def test_json_ld_is_authoritative(self):
		pages, soups = _pages(
			(
				"https://s.example",
				'<html><head><script type="application/ld+json">{"@type":"Organization","description":"Acme is a developer-tools company."}</script></head><body></body></html>',
			),
			(
				"https://s.example/about",
				"<html><head><meta name='description' content='Some about-page blurb.'></head><body></body></html>",
			),
		)
		desc = extractors.select_description(pages, soups)
		self.assertEqual(desc.method, Method.JSON_LD)


# --------------------------------------------------------------------------- #
# Contacts: emails + phones (mechanics)
# --------------------------------------------------------------------------- #
class EmailExtractionTest(UnitTestCase):
	def setUp(self):
		self.pages, _ = _pages(
			("https://acme.example", fixtures.HOMEPAGE),
			("https://acme.example/about", fixtures.ABOUT),
			("https://acme.example/contact", fixtures.CONTACT),
		)

	def test_emails_deduped_and_sourced(self):
		emails = extractors.extract_emails(self.pages)
		values = {e.value for e in emails}
		self.assertIn("hello@acme.example", values)
		self.assertIn("sales@acme.example", values)
		self.assertEqual(len(values), len(emails))  # deduped

	def test_blocklisted_noise_emails_rejected(self):
		pages, _ = _pages(
			("https://x.com", "<html><body>logo@2x.png test@example.com real@x.com</body></html>"),
		)
		values = {e.value for e in extractors.extract_emails(pages)}
		self.assertIn("real@x.com", values)
		self.assertNotIn("test@example.com", values)


class PhoneExtractionTest(UnitTestCase):
	def setUp(self):
		self.pages, _ = _pages(
			("https://acme.example", fixtures.HOMEPAGE),
			("https://acme.example/contact", fixtures.CONTACT),
		)

	def test_tel_link_marked(self):
		phones = extractors.extract_phones(self.pages)
		self.assertIn(Method.TEL_LINK, {p.method for p in phones})
		self.assertTrue(any("4155550142" in p.value.replace("+", "") for p in phones))


# --------------------------------------------------------------------------- #
# Social profiles (config-driven via Social rules)
# --------------------------------------------------------------------------- #
class SocialTest(UnitTestCase):
	def test_detects_networks_and_skips_share_links(self):
		page, soup = fixtures.make_page("https://acme.example", fixtures.HOMEPAGE)
		company = extractors.extract_company_info(page, soup)
		profiles = extractors.extract_social_profiles(
			[page], {page.url: soup}, fixtures.social_rules(), extra_links=company["social_links"]
		)
		self.assertTrue(profiles["linkedin"].value)
		self.assertTrue(profiles["github"].value)
		self.assertTrue(profiles["instagram"].value)
		# JSON-LD sameAs links win and are marked as such.
		self.assertEqual(profiles["linkedin"].method, Method.JSON_LD)
		# A facebook 'sharer' link must be ignored.
		self.assertEqual(profiles["facebook"].value, "")

	def test_protocol_relative_links_made_absolute(self):
		page, soup = fixtures.make_page(
			"https://bluedart.com",
			"<html><body><a href='//www.linkedin.com/company/bluedart/'>li</a>"
			"<a href='//twitter.com/BlueDart_'>tw</a></body></html>",
		)
		profiles = extractors.extract_social_profiles([page], {page.url: soup}, fixtures.social_rules())
		self.assertEqual(profiles["linkedin"].value, "https://www.linkedin.com/company/bluedart/")
		self.assertEqual(profiles["twitter"].value, "https://twitter.com/BlueDart_")


# --------------------------------------------------------------------------- #
# Industry classification (config-driven via Industry rules)
# --------------------------------------------------------------------------- #
class IndustryTest(UnitTestCase):
	def _classify(self, name, description, extra_html=""):
		page, _ = fixtures.make_page(
			"https://x.example",
			f"<html><head><title>{name}</title></head><body>{extra_html}</body></html>",
		)
		company = {"company_name": name, "description": description}
		return extractors.classify_industry([page], company, fixtures.industry_rules())

	def test_classifies_saas_or_crm_with_confidence(self):
		page, soup = fixtures.make_page("https://acme.example", fixtures.HOMEPAGE)
		company = extractors.extract_company_info(page, soup)
		industry, conf = extractors.classify_industry([page], company, fixtures.industry_rules())
		self.assertIn(industry, ("SaaS", "CRM"))
		self.assertGreater(conf, 0.0)
		self.assertLessEqual(conf, 1.0)

	def test_empty_site_returns_no_industry(self):
		page, _ = fixtures.make_page("https://e.example", fixtures.EMPTY)
		industry, conf = extractors.classify_industry([page], {}, fixtures.industry_rules())
		self.assertEqual(industry, "")
		self.assertEqual(conf, 0.0)

	def test_no_rules_returns_empty(self):
		page, _ = fixtures.make_page("https://e.example", fixtures.HOMEPAGE)
		self.assertEqual(extractors.classify_industry([page], {}, []), ("", 0.0))

	def test_d2c_brand_maps_to_ecommerce(self):
		self.assertEqual(self._classify("Gymshark", "Shop gym clothing and workout apparel.")[0], "Ecommerce")

	def test_beverage_brand_maps_to_food_and_beverage(self):
		self.assertEqual(
			self._classify("Liquid Death", "A beverage company with sparkling water and iced tea.")[0],
			"Food & Beverage",
		)

	def test_legal_help_beats_stray_keyword(self):
		self.assertEqual(
			self._classify(
				"Rocket Lawyer", "Rocket Lawyer makes legal help simple — legal documents and advice."
			)[0],
			"Legal",
		)

	def test_3d_printing_maps_to_manufacturing(self):
		# A "shop" nav link must not beat the core business signal in the headline.
		self.assertEqual(
			self._classify(
				"Desktop Metal",
				"Metal 3D printing and additive manufacturing for engineers.",
				"<nav>Shop</nav>",
			)[0],
			"Manufacturing",
		)


# --------------------------------------------------------------------------- #
# Generic rule executors directly
# --------------------------------------------------------------------------- #
class RuleExecutorTest(UnitTestCase):
	def test_apply_keyword_rules_weights_and_sums(self):
		rule = fixtures.keyword_rule(
			"Industry", ["saas", "subscription"], industry="SaaS", weight=2.0, match_scope="Headline"
		)
		scores = extractors.apply_keyword_rules({"Headline": "a saas subscription saas"}, [rule])
		# 3 hits * weight 2.0 = 6.0
		self.assertEqual(scores["SaaS"], 6.0)


# --------------------------------------------------------------------------- #
# Readability diagnosis (mechanics)
# --------------------------------------------------------------------------- #
class ReadabilityTest(UnitTestCase):
	def test_blocked_waf_challenge(self):
		page, _ = fixtures.make_page(
			"https://www.pepsi.com",
			'<html><head><script src="/_Incapsula_Resource?SWJIYLWA=1"></script></head><body></body></html>',
		)
		self.assertEqual(extractors.diagnose_readability([page]), "blocked")

	def test_empty_js_only_shell(self):
		page, _ = fixtures.make_page(
			"https://spa.example", "<html><head></head><body><div id='root'></div></body></html>"
		)
		self.assertEqual(extractors.diagnose_readability([page]), "empty")

	def test_unreachable_when_failed(self):
		page = CrawledPage(url="https://x.example", status_code=0, error="timeout after 10s")
		self.assertEqual(extractors.diagnose_readability([page]), "unreachable")

	def test_http_403_is_blocked(self):
		page = CrawledPage(
			url="https://www.pepperfry.com",
			status_code=403,
			html="<html><head><title>Access Denied</title></head></html>",
			text="Access Denied",
			title="Access Denied",
		)
		self.assertEqual(extractors.diagnose_readability([page]), "blocked")

	def test_readable_site_returns_empty_reason(self):
		page, _ = fixtures.make_page("https://acme.example", fixtures.HOMEPAGE)
		self.assertEqual(extractors.diagnose_readability([page]), "")
