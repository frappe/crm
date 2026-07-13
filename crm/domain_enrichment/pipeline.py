# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Orchestration: load config, crawl, run extractors, run enabled sources, assemble
an ``EnrichmentResult``.

``run()`` accepts an optional ``progress`` callback ``fn(step_index, message)`` so
Phase 4's ``tasks.py`` can surface the progress steps over realtime without the
engine depending on Frappe. The pipeline never writes to the DB or CRM docs (that
is Phase 4) and never raises for fetch/source failures -- they are captured as
errors/notes on the result.
"""

from __future__ import annotations

from dataclasses import replace
from urllib.parse import urlparse

from . import extractors
from .config import EnrichmentConfig, get_config
from .crawler import crawl, probe_about_pages
from .http import build_session
from .result import EnrichmentResult, Field, Method

# A preview only needs the document <head> (JSON-LD / OG / meta), which sits near the
# top -- cap the download well below the full run's max_download_bytes.
PREVIEW_MAX_DOWNLOAD_BYTES = 512_000

PROGRESS_STEPS = [
	"Discovering pages",
	"Crawling website",
	"Extracting company information",
	"Extracting contacts",
	"Classifying industry",
	"Saving results",
	"Completed",
]


def _normalize_website(url: str) -> str:
	url = (url or "").strip()
	if not url:
		raise ValueError("website URL is required")
	if not urlparse(url).scheme:
		url = "https://" + url
	parsed = urlparse(url)
	if parsed.scheme not in ("http", "https"):
		raise ValueError(f"unsupported URL scheme: {parsed.scheme}")
	if not parsed.netloc:
		raise ValueError(f"invalid URL: {url}")
	return url


def preview(website: str, cfg: EnrichmentConfig = None) -> EnrichmentResult:
	"""Fast, metadata-only prefill for the create-record modal.

	Fetches ONLY the homepage and reads ONLY the metadata the site declares about
	itself in its ``<head>`` -- JSON-LD / Open Graph / meta tags / favicon, plus the
	JSON-LD ``sameAs`` social links. It deliberately does NOT run the body-text
	extractors (description body-scan, emails, phones) or the industry classifier:
	those are the full ``run`` path's job, which fires as a background job once the
	record is saved, so spending synchronous request time on them here is wasted work.

	Homepage-only (no crawl), short timeout, small download cap. SSRF is enforced by
	``fetch`` inside ``crawl``. Never raises -- failures land in ``result.notes``.
	"""
	website = _normalize_website(website)
	cfg = cfg or get_config()
	result = EnrichmentResult(website=website)

	# Bounded fetch: short preview timeout + head-sized download cap, homepage only.
	fetch_cfg = replace(
		cfg,
		settings={
			**cfg.settings,
			"request_timeout": cfg.setting("preview_timeout", 8),
			"max_download_bytes": PREVIEW_MAX_DOWNLOAD_BYTES,
			"max_pages": 1,
			"max_depth": 0,
		},
	)

	crawled = crawl(website, fetch_cfg)
	homepage, home_soup = crawled[0] if crawled else (None, None)
	if home_soup is None:
		result.notes.append(
			(homepage.error if homepage else "") or extractors.READABILITY_MESSAGES["unreachable"]
		)
		return result

	# Metadata only: name / description / logo / sameAs social links from the <head>.
	company = extractors.extract_company_info(homepage, home_soup)
	result.company_name = company.get("company_name") or Field()
	result.description = company.get("description") or Field()
	result.logo = company.get("logo") or Field()
	result.social_profiles = extractors.extract_social_profiles(
		[], {}, cfg.rules("Social"), extra_links=company.get("social_links")
	)
	return result


def run(website: str, cfg: EnrichmentConfig = None, progress=None) -> EnrichmentResult:
	"""Run the full enrichment engine for ``website`` and return the result.

	:param website: the site to enrich (scheme optional; https assumed).
	:param cfg: an :class:`EnrichmentConfig`; loaded via ``get_config()`` if omitted.
	:param progress: optional ``fn(step_index, message)`` callback (0-based index
	    into ``PROGRESS_STEPS``); exceptions in it are swallowed.
	"""
	website = _normalize_website(website)
	cfg = cfg or get_config()
	result = EnrichmentResult(website=website)

	def emit(step_index, message=""):
		if progress:
			try:
				progress(step_index, message or PROGRESS_STEPS[step_index])
			except Exception:
				pass  # progress reporting must never break enrichment

	session = build_session(cfg)
	try:
		# 1 + 2. Discover + crawl (BFS does both; reported together).
		emit(0)
		crawled = crawl(website, cfg, session=session, progress=lambda msg: emit(1, msg))
		pages = [page for page, _soup in crawled]
		soups_by_url = {page.url: soup for page, soup in crawled}
		result.pages_crawled = [{"url": p.url, "status": p.status_code, "error": p.error} for p in pages]
		result.errors = [{"url": p.url, "error": p.error} for p in pages if p.error]

		# Short-circuit on a blocked / unreachable homepage with a clear reason.
		reason = extractors.diagnose_readability(pages)
		if reason in ("blocked", "unreachable"):
			result.notes.append(extractors.READABILITY_MESSAGES[reason])
			emit(6)
			return result
		if reason == "empty":
			# JS-rendered body: <head> metadata may still be usable -- fall through.
			result.notes.append(extractors.READABILITY_MESSAGES["empty"])

		homepage = pages[0]
		home_soup = soups_by_url.get(homepage.url)

		# If the BFS didn't surface an About page, probe the common paths -- it's the
		# best source of a company description (and helps industry/contacts too). Only
		# when the page budget allows more fetches, so the synchronous preview
		# (max_pages=1) doesn't tie up a web worker on extra probes.
		max_pages = int(cfg.setting("max_pages", 10) or 10)
		if home_soup and len(pages) < max_pages and not any(extractors._is_about_page(p.url) for p in pages):
			for page, soup in probe_about_pages(
				homepage.url, cfg, session=session, skip_urls=[p.url for p in pages]
			):
				pages.append(page)
				soups_by_url[page.url] = soup
				result.pages_crawled.append(
					{"url": page.url, "status": page.status_code, "error": page.error}
				)

		# 3. Company information (each field carries provenance).
		emit(2)
		company = extractors.extract_company_info(homepage, home_soup) if home_soup else {}
		result.company_name = company.get("company_name") or Field()
		result.logo = company.get("logo") or Field()
		result.description = (
			extractors.select_description(pages, soups_by_url) or company.get("description") or Field()
		)

		# 4. Contacts: emails, phones, social.
		emit(3)
		result.emails = extractors.extract_emails(pages)
		result.phones = extractors.extract_phones(pages)
		result.social_profiles = extractors.extract_social_profiles(
			pages,
			soups_by_url,
			cfg.rules("Social"),
			extra_links=company.get("social_links"),
		)

		# 5. Industry.
		emit(4)
		industry, confidence = extractors.classify_industry(pages, company, cfg.rules("Industry"))
		result.industry = Field(industry, website, Method.KEYWORD_CLASSIFIER) if industry else Field()
		result.industry_confidence = confidence

		# 6 + 7. Done (saving handled by the caller in Phase 4).
		emit(5)
		emit(6)
		return result
	finally:
		session.close()
