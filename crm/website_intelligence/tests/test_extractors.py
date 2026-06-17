"""Network-free unit tests for the Website Intelligence extractors and crawler.

Run standalone (no Frappe, no pytest needed):
    python -m unittest crm.website_intelligence.tests.test_extractors
or from the package dir:
    python -m unittest discover -s tests
"""

import os
import sys
import unittest

from bs4 import BeautifulSoup

# Make the package importable whether run via bench or standalone.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from website_intelligence import extractors  # noqa: E402
from website_intelligence.crawler import (  # noqa: E402
    extract_content, normalize_url, same_site, _link_priority, _is_crawlable,
)
from website_intelligence.models import CrawledPage, Method  # noqa: E402
from website_intelligence.tests import fixtures  # noqa: E402


def make_page(url, html):
    soup = BeautifulSoup(html, "html.parser")
    content = extract_content(BeautifulSoup(html, "html.parser"))
    return CrawledPage(url=url, status_code=200, html=html,
                       text=content["text"], title=content["title"],
                       headings=content["headings"]), soup


class CrawlerHelpersTest(unittest.TestCase):
    def test_normalize_url_strips_fragment_and_trailing_slash(self):
        self.assertEqual(normalize_url("https://x.com/about/#team"), "https://x.com/about")
        self.assertEqual(normalize_url("https://x.com/"), "https://x.com/")

    def test_same_site_ignores_www_and_subdomains(self):
        self.assertTrue(same_site("https://www.x.com/a", "x.com"))
        self.assertTrue(same_site("https://blog.x.com/a", "x.com"))
        self.assertFalse(same_site("https://other.com/a", "x.com"))

    def test_priority_ranks_about_contact_first(self):
        self.assertLess(_link_priority("https://x.com/about", "About"),
                        _link_priority("https://x.com/blog/post", "Post"))

    def test_is_crawlable_rejects_assets_and_schemes(self):
        self.assertFalse(_is_crawlable("mailto:a@b.com"))
        self.assertFalse(_is_crawlable("https://x.com/file.pdf"))
        self.assertTrue(_is_crawlable("https://x.com/about"))


class CompanyInfoTest(unittest.TestCase):
    def setUp(self):
        self.page, self.soup = make_page("https://acme.example", fixtures.HOMEPAGE)

    def test_prefers_json_ld_for_name(self):
        info = extractors.extract_company_info(self.page, self.soup)
        self.assertEqual(info["company_name"].value, "Acme Analytics Inc.")
        self.assertEqual(info["company_name"].method, Method.JSON_LD)
        self.assertEqual(info["company_name"].source, "https://acme.example")

    def test_description_from_json_ld(self):
        info = extractors.extract_company_info(self.page, self.soup)
        self.assertIn("analytics", info["description"].value.lower())

    def test_select_description_prefers_about_over_product_homepage(self):
        home = make_page(
            "https://shop.example",
            "<html><head><meta property='og:description'"
            " content='Shop the latest gadgets and accessories.'></head><body></body></html>")
        about = make_page(
            "https://shop.example/about",
            "<html><head><meta name='description'"
            " content='Acme builds developer tools for teams.'></head><body></body></html>")
        pages = [home[0], about[0]]
        soups = {home[0].url: home[1], about[0].url: about[1]}
        desc = extractors.select_description(pages, soups)
        self.assertEqual(desc.value, "Acme builds developer tools for teams.")
        self.assertEqual(desc.source, "https://shop.example/about")

    def test_select_description_falls_back_to_homepage(self):
        home = make_page(
            "https://x.example",
            "<html><head><meta property='og:description'"
            " content='We make great software.'></head><body></body></html>")
        desc = extractors.select_description([home[0]], {home[0].url: home[1]})
        self.assertEqual(desc.value, "We make great software.")

    def test_json_ld_is_authoritative(self):
        home = make_page(
            "https://s.example",
            '<html><head><script type="application/ld+json">'
            '{"@type":"Organization","description":"Acme is a developer-tools company."}'
            "</script></head><body></body></html>")
        about = make_page(
            "https://s.example/about",
            "<html><head><meta name='description' content='Some about-page blurb.'>"
            "</head><body></body></html>")
        pages = [home[0], about[0]]
        soups = {home[0].url: home[1], about[0].url: about[1]}
        desc = extractors.select_description(pages, soups)
        self.assertEqual(desc.method, Method.JSON_LD)

    def test_homepage_noncommerce_beats_about_subpages(self):
        # The NVIDIA case: a good homepage tagline should win over noisy /about/* pages.
        home = make_page(
            "https://n.example",
            "<html><head><meta property='og:description'"
            " content='We build the fastest computing platforms on earth.'>"
            "</head><body></body></html>")
        webinars = make_page(
            "https://n.example/about-n/webinar-portal",
            "<html><head><meta name='description'"
            " content='Take a deep dive into our webinars and learn on demand about lots of topics here.'>"
            "</head><body></body></html>")
        pages = [home[0], webinars[0]]
        soups = {home[0].url: home[1], webinars[0].url: webinars[1]}
        desc = extractors.select_description(pages, soups)
        self.assertEqual(desc.source, "https://n.example")
        self.assertIn("computing", desc.value)

    def test_prefers_longer_among_equal_about_pages(self):
        # Homepage is a storefront pitch (penalised), so the About pages compete;
        # among equal About pages the longer/more substantive text wins.
        home = make_page("https://m.example",
                         "<html><head><meta property='og:description'"
                         " content='Shop our products now.'></head><body></body></html>")
        a1 = make_page("https://m.example/about",
                       "<html><head><meta name='description' content='Learn about us.'>"
                       "</head><body></body></html>")
        a2 = make_page("https://m.example/company",
                       "<html><head><meta name='description'"
                       " content='Our mission is to build the future of human connection "
                       "and the technology that makes it possible.'></head><body></body></html>")
        pages = [home[0], a1[0], a2[0]]
        soups = {home[0].url: home[1], a1[0].url: a1[1], a2[0].url: a2[1]}
        desc = extractors.select_description(pages, soups)
        self.assertIn("mission", desc.value)

    def test_logo_falls_back_to_favicon_ico(self):
        # The homepage fixture declares no <link rel="icon">, so we fall back to
        # the conventional /favicon.ico on the same origin.
        info = extractors.extract_company_info(self.page, self.soup)
        self.assertEqual(info["logo"].method, Method.FAVICON)
        self.assertEqual(info["logo"].value, "https://acme.example/favicon.ico")

    def test_logo_prefers_declared_apple_touch_icon(self):
        page, soup = make_page(
            "https://x.example",
            "<html><head>"
            "<link rel='icon' href='/fav.png' sizes='16x16'>"
            "<link rel='apple-touch-icon' href='/touch.png'>"
            "</head><body></body></html>")
        info = extractors.extract_company_info(page, soup)
        self.assertEqual(info["logo"].value, "https://x.example/touch.png")
        self.assertEqual(info["logo"].method, Method.FAVICON)

    def test_company_name_strips_tagline(self):
        page, soup = make_page(
            "https://p.example",
            "<html><head>"
            "<meta property='og:title' content='PostHog – dev tools'>"
            "</head><body></body></html>")
        info = extractors.extract_company_info(page, soup)
        self.assertEqual(info["company_name"].value, "PostHog")

    def test_company_name_trims_sentence_title(self):
        # itcportal.com case: a descriptive og:title must not become the name.
        self.assertEqual(
            extractors._clean_company_name(
                "ITC Ltd has diversified presence in FMCG, Paperboards & Packaging"),
            "ITC Ltd")
        self.assertEqual(
            extractors._clean_company_name("Acme Corp provides cloud security"),
            "Acme Corp")

    def test_company_name_brand_at_end_matches_domain(self):
        # 8848digital.com: title is "Tagline | Brand"; the brand matches the domain.
        self.assertEqual(
            extractors._clean_company_name(
                "Innovative IT & Software Development Services | 8848 Digital",
                "https://8848digital.com/"),
            "8848 Digital")
        # Without the domain hint, it falls back to the first chunk (old behaviour).
        self.assertEqual(
            extractors._clean_company_name(
                "Innovative IT & Software Development Services | 8848 Digital"),
            "Innovative IT & Software Development Services")
        # Brand-first titles are unaffected by the domain hint.
        self.assertEqual(
            extractors._clean_company_name("PostHog – dev tools", "https://posthog.com"),
            "PostHog")

    def test_meta_fallback_when_no_json_ld(self):
        page, soup = make_page("https://x.example",
                               "<html><head><title>Foo</title>"
                               "<meta property='og:site_name' content='Foo Inc'>"
                               "</head><body></body></html>")
        info = extractors.extract_company_info(page, soup)
        self.assertEqual(info["company_name"].value, "Foo Inc")
        self.assertEqual(info["company_name"].method, Method.META_TAG)

    def test_broken_json_ld_does_not_crash(self):
        page, soup = make_page("https://b.example", fixtures.BROKEN_JSON_LD)
        info = extractors.extract_company_info(page, soup)
        # Falls back to title tag.
        self.assertEqual(info["company_name"].method, Method.TITLE_TAG)


class ContactsTest(unittest.TestCase):
    def setUp(self):
        self.pages = [
            make_page("https://acme.example", fixtures.HOMEPAGE)[0],
            make_page("https://acme.example/about", fixtures.ABOUT)[0],
            make_page("https://acme.example/contact", fixtures.CONTACT)[0],
        ]

    def test_emails_deduped_and_sourced(self):
        emails = extractors.extract_emails(self.pages)
        values = {e.value for e in emails}
        self.assertIn("hello@acme.example", values)
        self.assertIn("sales@acme.example", values)
        # Deduped: each value appears once.
        self.assertEqual(len(values), len(emails))
        self.assertTrue(all(e.method == Method.REGEX for e in emails))

    def test_phone_from_tel_link_marked(self):
        phones = extractors.extract_phones(self.pages)
        methods = {p.method for p in phones}
        self.assertIn(Method.TEL_LINK, methods)
        self.assertTrue(any("4155550142" in p.value.replace("+", "") for p in phones))

    def test_addresses_from_json_ld_high_confidence(self):
        soups = {self.pages[0].url: make_page(self.pages[0].url, fixtures.HOMEPAGE)[1]}
        company = extractors.extract_company_info(
            self.pages[0], soups[self.pages[0].url])
        addrs = extractors.extract_addresses(self.pages, soups, company)
        self.assertTrue(addrs)
        self.assertGreaterEqual(addrs[0].confidence, 0.85)
        self.assertEqual(addrs[0].method, Method.JSON_LD)


class TeamTest(unittest.TestCase):
    def test_only_real_people_with_adjacent_titles(self):
        page, soup = make_page("https://acme.example/about", fixtures.ABOUT)
        contacts = extractors.discover_team_members([page], {page.url: soup})
        names = {c.name for c in contacts}
        self.assertIn("Jane Doe", names)
        self.assertIn("John Smith", names)
        # False positives must be rejected.
        self.assertNotIn("Senior Vice President", names)
        self.assertNotIn("About Acme", names)
        self.assertTrue(all(c.method == Method.TEAM_RULE for c in contacts))

    def test_director_not_misread_as_cto(self):
        # "Director" contains the substring "cto" — must not tag the person CTO.
        self.assertEqual(extractors._designation_in("Rajesh Kabra Director"), "Director")
        self.assertEqual(extractors._designation_in("Jane Doe CTO"), "CTO")
        self.assertEqual(
            extractors._designation_in("Sanjay Taparia Chief Executive Officer"),
            "Chief Executive Officer")

    def test_company_names_rejected_as_people(self):
        for name in ("Summit Securities Limited", "Secure Meters Limited",
                     "Acme Holdings", "Acme Industries"):
            self.assertFalse(extractors._looks_like_name(name), name)
        for name in ("Rajesh Kabra", "Bhagwat Singh Babel", "Jyoti Davar Vij"):
            self.assertTrue(extractors._looks_like_name(name), name)

    def test_form_controls_are_not_team_members(self):
        # A contact page's country <select> and enquiry-type <option>/<label>
        # must not be scooped up as people (the rrkabel.com case).
        html = (
            "<html><body><main>"
            "<div><p>Jane Doe</p><span>Director</span></div>"
            "<form>"
            "  <label>Customer Complaints</label>"
            "  <select><option>Costa Rica</option></select>"
            "  <select name='type'><option>Enquiry Type</option>"
            "    <option>Lead</option></select>"
            "</form>"
            "</main></body></html>")
        page, soup = make_page("https://acme.example/contact-us", html)
        names = {c.name for c in extractors.discover_team_members([page], {page.url: soup})}
        self.assertNotIn("Costa Rica", names)
        self.assertNotIn("Enquiry Type", names)
        self.assertNotIn("Customer Complaints", names)


class SocialTest(unittest.TestCase):
    def test_detects_networks_and_skips_share_links(self):
        page, soup = make_page("https://acme.example", fixtures.HOMEPAGE)
        company = extractors.extract_company_info(page, soup)
        profiles = extractors.extract_social_profiles(
            [page], {page.url: soup}, extra_links=company["social_links"])
        self.assertTrue(profiles["linkedin"].value)
        self.assertTrue(profiles["github"].value)
        self.assertTrue(profiles["instagram"].value)
        # JSON-LD sameAs links should win and be marked as such.
        self.assertEqual(profiles["linkedin"].method, Method.JSON_LD)
        # Facebook 'sharer' link must be ignored.
        self.assertEqual(profiles["facebook"].value, "")

    def test_protocol_relative_links_are_made_absolute(self):
        # bluedart.com case: hrefs like "//www.linkedin.com/company/x" must become
        # absolute https URLs, not be stored/rendered as broken "//..." links.
        page, soup = make_page(
            "https://bluedart.com",
            "<html><body>"
            "<a href='//www.linkedin.com/company/bluedart/'>li</a>"
            "<a href='//twitter.com/BlueDart_'>tw</a>"
            "</body></html>")
        profiles = extractors.extract_social_profiles([page], {page.url: soup})
        self.assertEqual(profiles["linkedin"].value,
                         "https://www.linkedin.com/company/bluedart/")
        self.assertEqual(profiles["twitter"].value, "https://twitter.com/BlueDart_")


class TechnologyTest(unittest.TestCase):
    def test_detects_nextjs_ga_and_wordpress(self):
        home, _ = make_page("https://acme.example", fixtures.HOMEPAGE)
        techs = {t.name for t in extractors.detect_technologies([home])}
        self.assertIn("Next.js", techs)
        self.assertIn("Google Analytics", techs)

        wp, _ = make_page("https://wp.example", fixtures.WORDPRESS)
        wp_techs = {t.name for t in extractors.detect_technologies([wp])}
        self.assertIn("WordPress", wp_techs)


class SignalsTest(unittest.TestCase):
    def test_hiring_funding_ai_signals(self):
        pages = [make_page("https://acme.example", fixtures.HOMEPAGE)[0],
                 make_page("https://acme.example/about", fixtures.ABOUT)[0]]
        signals = extractors.detect_signals(pages)
        self.assertTrue(signals.hiring)
        self.assertTrue(signals.funding)
        self.assertTrue(signals.ai)
        self.assertTrue(signals.matched_snippets)
        # Every snippet is traceable to a source page.
        self.assertTrue(all(s["source"] for s in signals.matched_snippets))


class EmployeesTest(unittest.TestCase):
    def _bucket(self, html):
        page, _ = make_page("https://e.example/about", html)
        return extractors.estimate_employees([page]).value

    def test_team_of_phrase(self):
        self.assertEqual(self._bucket("<p>We are a team of 50 builders.</p>"), "11-50")

    def test_plus_employees_phrase(self):
        self.assertEqual(self._bucket("<p>Join 200+ employees worldwide.</p>"), "51-200")

    def test_over_n_people(self):
        self.assertEqual(self._bucket("<p>More than 1,200 people work here.</p>"), "1000+")

    def test_picks_largest_plausible(self):
        html = "<p>Our design team of 6. Overall 300 employees.</p>"
        self.assertEqual(self._bucket(html), "201-500")

    def test_no_phrase_returns_empty(self):
        self.assertEqual(self._bucket("<p>We build great software.</p>"), "")

    def test_ignores_non_employee_numbers(self):
        # "10,000 customers" must not be read as headcount.
        self.assertEqual(self._bucket("<p>Trusted by 10,000 customers.</p>"), "")

    def test_team_members_counts_as_strong(self):
        # The Supabase-style "280+ team members" should bucket correctly.
        self.assertEqual(
            self._bucket("<p>280+ team members in 55+ countries.</p>"), "201-500")

    def test_strong_keyword_beats_larger_weak_phrase(self):
        # A reliable "50 employees" wins over an ambiguous "team of 5000".
        html = "<p>Join our team of 5000 fans. We are 50 employees.</p>"
        self.assertEqual(self._bucket(html), "11-50")


class IndustryTest(unittest.TestCase):
    def test_classifies_saas_or_crm_with_confidence(self):
        page, soup = make_page("https://acme.example", fixtures.HOMEPAGE)
        company = extractors.extract_company_info(page, soup)
        industry, conf = extractors.classify_industry([page], company)
        self.assertIn(industry, ("SaaS", "CRM"))
        self.assertGreater(conf, 0.0)
        self.assertLessEqual(conf, 1.0)

    def test_empty_site_returns_no_industry(self):
        page, _ = make_page("https://e.example", fixtures.EMPTY)
        industry, conf = extractors.classify_industry([page], {})
        self.assertEqual(industry, "")
        self.assertEqual(conf, 0.0)

    def _classify(self, name, description):
        """Classify off the stable identity fields the way real sites carry them."""
        page, _ = make_page("https://x.example",
                            f"<html><head><title>{name}</title></head><body></body></html>")
        company = {"company_name": name, "description": description}
        return extractors.classify_industry([page], company)[0]

    def test_d2c_brand_descriptions_map_to_ecommerce(self):
        # Consumer brands describe products, not "ecommerce platforms" — the
        # retail signals (shop / free shipping / apparel) must still register.
        self.assertEqual(
            self._classify("Gymshark", "Shop gym clothing and workout apparel."),
            "Ecommerce")
        self.assertEqual(
            self._classify("Brooklinen", "Shop soft sheets. Free shipping and free returns."),
            "Ecommerce")

    def test_beverage_brand_maps_to_food_and_beverage(self):
        self.assertEqual(
            self._classify("Liquid Death",
                           "A better-for-you beverage company with sparkling water and iced tea."),
            "Food & Beverage")
        self.assertEqual(
            self._classify("Magic Spoon", "High-protein, keto-friendly cereal."),
            "Food & Beverage")

    def test_news_publisher_maps_to_media(self):
        self.assertEqual(
            self._classify("404 Media",
                           "An independent media company founded by technology journalists."),
            "Media")

    def test_legal_help_beats_property_keyword(self):
        # rocketlawyer regression: "legal help" must outweigh a stray "property".
        self.assertEqual(
            self._classify("Rocket Lawyer",
                           "Rocket Lawyer makes legal help simple — legal documents and advice."),
            "Legal")

    def test_3d_printing_maps_to_manufacturing_not_ecommerce(self):
        # desktopmetal regression: a "shop" nav link must not beat the core business.
        page, _ = make_page(
            "https://x.example",
            "<html><head><title>Desktop Metal</title></head>"
            "<body><nav>Shop</nav></body></html>")
        company = {"company_name": "Desktop Metal",
                   "description": "Metal 3D printing and additive manufacturing for engineers."}
        self.assertEqual(extractors.classify_industry([page], company)[0], "Manufacturing")


class ReadabilityTest(unittest.TestCase):
    def test_blocked_waf_challenge(self):
        # Incapsula-style challenge page (the pepsi.com case).
        page, _ = make_page(
            "https://www.pepsi.com",
            '<html><head><script src="/_Incapsula_Resource?SWJIYLWA=1"></script>'
            "</head><body></body></html>")
        self.assertEqual(extractors.diagnose_readability([page]), "blocked")

    def test_empty_js_only_shell(self):
        page, _ = make_page("https://spa.example",
                            "<html><head></head><body><div id='root'></div></body></html>")
        self.assertEqual(extractors.diagnose_readability([page]), "empty")

    def test_unreachable_when_all_failed(self):
        page = CrawledPage(url="https://x.example", status_code=0,
                           error="timeout after 10s")
        self.assertEqual(extractors.diagnose_readability([page]), "unreachable")

    def test_http_403_access_denied_is_blocked(self):
        # pepperfry.com case: a 403 "Access Denied" page must not be read as content.
        page = CrawledPage(url="https://www.pepperfry.com", status_code=403,
                           html="<html><head><title>Access Denied</title></head></html>",
                           text="Access Denied", title="Access Denied")
        self.assertEqual(extractors.diagnose_readability([page]), "blocked")

    def test_readable_site_returns_empty_reason(self):
        page, _ = make_page("https://acme.example", fixtures.HOMEPAGE)
        self.assertEqual(extractors.diagnose_readability([page]), "")


if __name__ == "__main__":
    unittest.main(verbosity=2)
