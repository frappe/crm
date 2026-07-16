# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Offline HTML fixtures + in-memory config builders for network-free tests.

The HTML fixtures are deterministic snapshots used by the pure unit tests so the
crawler/extractor mechanics can be exercised without touching the network. The
config builders assemble ``Rule`` / ``Mapping`` / ``EnrichmentConfig`` objects in
memory (no DB) so the rule executors can be tested rule-driven, exactly as the
engine would see them after ``get_config()`` — but without hitting Frappe.
"""

from __future__ import annotations

import re

from bs4 import BeautifulSoup

from crm.domain_enrichment.config import EnrichmentConfig, Mapping, Rule
from crm.domain_enrichment.crawler import extract_content
from crm.domain_enrichment.result import CrawledPage

# --------------------------------------------------------------------------- #
# HTML fixtures
# --------------------------------------------------------------------------- #
HOMEPAGE = """
<!doctype html>
<html>
<head>
  <title>Acme Analytics | AI powered SaaS</title>
  <meta name="description" content="Acme is an AI powered analytics platform.">
  <meta property="og:site_name" content="Acme Analytics">
  <meta property="og:description" content="Real-time analytics for modern teams.">
  <meta property="og:image" content="https://acme.example/logo.png">
  <script type="application/ld+json">
  {
    "@context": "https://schema.org",
    "@type": "Organization",
    "name": "Acme Analytics Inc.",
    "description": "AI powered analytics SaaS for product teams.",
    "logo": {"url": "https://acme.example/ld-logo.png"},
    "sameAs": [
      "https://www.linkedin.com/company/acme-analytics",
      "https://twitter.com/acmeanalytics",
      "https://github.com/acme"
    ]
  }
  </script>
  <script src="/_next/static/chunk.js"></script>
  <script src="https://www.googletagmanager.com/gtag/js?id=G-XXededXX"></script>
</head>
<body>
  <h1>AI powered analytics</h1>
  <h2>We are hiring across engineering</h2>
  <nav>
    <a href="/about">About</a>
    <a href="/contact">Contact</a>
    <a href="/team">Team</a>
    <a href="/careers">Careers</a>
    <a href="https://facebook.com/sharer?u=x">Share</a>
    <a href="https://instagram.com/acmeanalytics">Instagram</a>
    <a href="https://external-site.com/page">External</a>
  </nav>
  <p>Contact us at hello@acme.example or call <a href="tel:+1 415 555 0142">us</a>.</p>
  <p>Our subscription pricing plans start free. Customer relationship tooling.</p>
</body>
</html>
"""

ABOUT = """
<!doctype html>
<html><head><title>About Acme</title></head>
<body>
  <h1>About Acme</h1>
  <p>We raised a Series A round and are backed by great investors.</p>
  <div class="team">
    <div class="member"><div class="name">Jane Doe</div><div class="role">CEO &amp; Co-Founder</div></div>
    <div class="member"><div class="name">John Smith</div><div class="role">CTO</div></div>
    <div class="member"><div class="name">Senior Vice President</div><div class="role">VP</div></div>
    <div class="member"><div class="name">About Acme</div><div class="role">Director</div></div>
  </div>
  <p>Reach finance at billing@acme.example.</p>
</body></html>
"""

CONTACT = """
<!doctype html>
<html><head><title>Contact Acme</title></head>
<body>
  <h1>Contact</h1>
  <p>Head office: 100 Market St, San Francisco, CA, 94103, United States</p>
  <p>Email: sales@acme.example</p>
  <p>Phone: +1 (415) 555-0199</p>
</body></html>
"""

WORDPRESS = """
<html><head><meta name="generator" content="WordPress 6.4"></head>
<body><img src="/wp-content/uploads/x.png"><script src="/wp-json/index.js"></script></body></html>
"""

EMPTY = "<html><head></head><body></body></html>"

# A JavaScript-only SPA shell (e.g. a Vite/React build). The body is an empty mount
# point; everything meaningful is rendered client-side, so requests + BeautifulSoup
# see only the build-tool-default title and favicon -- no description, og, or JSON-LD.
JS_SPA_SHELL = """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Vite App</title>
    <script type="module" crossorigin src="/assets/index-5d175413.js"></script>
    <link rel="stylesheet" href="/assets/index-57b7cd59.css">
    <script type="module">window.onerror = () => {};</script>
  </head>
  <body>
    <div id="root"></div>
  </body>
</html>
"""

BROKEN_JSON_LD = """
<html><head>
<script type="application/ld+json">{ this is not valid json ]</script>
<title>Broken Co</title>
</head><body><h1>Broken</h1></body></html>
"""

# --------------------------------------------------------------------------- #
# Sitemap fixtures
# --------------------------------------------------------------------------- #
URLSET_XML = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://acme.example/about</loc></url>
  <url><loc>https://acme.example/contact</loc></url>
  <url><loc>https://acme.example/blog/post-1</loc></url>
</urlset>"""

SITEMAP_INDEX_XML = """<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <sitemap><loc>https://acme.example/sitemap-pages.xml</loc></sitemap>
  <sitemap><loc>https://acme.example/sitemap-blog.xml</loc></sitemap>
</sitemapindex>"""

# A sitemap trying to smuggle a DTD entity-expansion payload -- must be rejected
# outright by _parse_sitemap before ET.fromstring ever sees it.
MALICIOUS_DOCTYPE_XML = """<?xml version="1.0"?>
<!DOCTYPE foo [<!ENTITY xxe "boom">]>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://acme.example/&xxe;</loc></url>
</urlset>"""


def fake_fetch(responses):
	"""Build a ``fetch(url, cfg, session=None, html_only=True)`` stub keyed by exact URL.

	``responses`` maps url -> (status, body) for a 200-shaped response. A URL absent
	from the map behaves like a 404 (mirrors a missing sitemap/robots.txt), so tests
	only need to declare the endpoints they care about.
	"""

	def fake(url, cfg, session=None, html_only=True):
		entry = responses.get(url)
		if entry is None:
			return 404, "", "not found", url
		status, body = entry
		return status, body, "", url

	return fake


# --------------------------------------------------------------------------- #
# Page helper
# --------------------------------------------------------------------------- #
def make_page(url, html, status_code=200):
	"""Build a (CrawledPage, soup) pair from raw HTML, exactly as the crawler does.

	``extract_content`` mutates its soup, so it is given a throwaway parse and the
	returned ``soup`` is a fresh, unmutated DOM (mirrors ``crawler.crawl_page``).
	"""
	soup = BeautifulSoup(html, "html.parser")
	content = extract_content(BeautifulSoup(html, "html.parser"))
	page = CrawledPage(
		url=url,
		status_code=status_code,
		html=html,
		text=content["text"],
		title=content["title"],
		headings=content["headings"],
	)
	return page, soup


# --------------------------------------------------------------------------- #
# In-memory rule builders (no DB) — mirror what config._build_rules() produces
# --------------------------------------------------------------------------- #
def _compile(pattern, is_regex):
	if is_regex:
		return re.compile(pattern, re.IGNORECASE)
	return re.compile(re.escape(pattern), re.IGNORECASE)


def keyword_rule(rule_type, patterns, *, target_value="", industry="", weight=1.0, match_scope="Full Text"):
	"""Build a substring keyword Rule directly (is_regex=0 for each pattern)."""
	compiled = [(_compile(p, False), p) for p in patterns]
	return Rule(
		rule_type=rule_type,
		target_value=target_value,
		industry=industry,
		weight=weight,
		match_scope=match_scope,
		patterns=compiled,
	)


def regex_rule(rule_type, patterns, *, target_value="", weight=1.0, match_scope="HTML"):
	"""Build a regex Rule directly (is_regex=1 for each pattern)."""
	compiled = [(_compile(p, True), p) for p in patterns]
	return Rule(
		rule_type=rule_type,
		target_value=target_value,
		weight=weight,
		match_scope=match_scope,
		patterns=compiled,
	)


def industry_rules():
	"""A small set of Industry rules (Headline scope) covering the fixtures."""
	return [
		keyword_rule(
			"Industry",
			["saas", "software as a service", "subscription"],
			industry="SaaS",
			match_scope="Headline",
		),
		keyword_rule(
			"Industry",
			["crm", "customer relationship"],
			industry="CRM",
			match_scope="Headline",
		),
		keyword_rule(
			"Industry",
			["shop", "free shipping", "apparel", "ecommerce"],
			industry="Ecommerce",
			match_scope="Headline",
		),
		keyword_rule(
			"Industry",
			["beverage", "sparkling water", "iced tea", "cereal"],
			industry="Food & Beverage",
			match_scope="Headline",
		),
		keyword_rule(
			"Industry",
			["3d printing", "additive manufacturing", "manufacturing"],
			industry="Manufacturing",
			match_scope="Headline",
		),
		keyword_rule(
			"Industry",
			["legal help", "legal documents", "legal advice", "law firm"],
			industry="Legal",
			match_scope="Headline",
		),
		keyword_rule(
			"Industry",
			["media company", "journalists", "newsroom"],
			industry="Media",
			match_scope="Headline",
		),
	]


def social_rules():
	return [
		regex_rule("Social", [r"linkedin\.com/(company|in|school)/"], target_value="linkedin"),
		regex_rule("Social", [r"(twitter\.com|x\.com)/[A-Za-z0-9_]+"], target_value="twitter"),
		regex_rule("Social", [r"github\.com/[A-Za-z0-9_.-]+"], target_value="github"),
		regex_rule("Social", [r"facebook\.com/[A-Za-z0-9_.\-/]+"], target_value="facebook"),
		regex_rule("Social", [r"instagram\.com/[A-Za-z0-9_.]+"], target_value="instagram"),
	]


def make_config(settings=None, **kwargs) -> EnrichmentConfig:
	"""Assemble an in-memory ``EnrichmentConfig`` for the SSRF / engine tests."""
	cfg = EnrichmentConfig(settings=settings or {})
	for key, value in kwargs.items():
		setattr(cfg, key, value)
	return cfg


def make_mapping(source_key, target_doctype, target_fieldname, write_policy="Fill if empty", **kwargs):
	return Mapping(
		source_key=source_key,
		target_doctype=target_doctype,
		target_fieldname=target_fieldname,
		write_policy=write_policy,
		create_missing_link=kwargs.get("create_missing_link", 0),
		default_values=kwargs.get("default_values", ""),
	)
