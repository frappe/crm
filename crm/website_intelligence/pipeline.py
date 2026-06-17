"""Orchestration: crawl a site, run every extractor, assemble EnrichmentResult.

The pipeline accepts an optional `progress` callback `fn(step_index, message)` so
both the CLI and the Frappe background job can surface the 9 progress steps from
the spec without the core depending on Frappe.
"""

from __future__ import annotations

from urllib.parse import urlparse

from . import extractors
from . import wikipedia
from .crawler import discover_relevant_pages
from .http_client import build_session
from .models import EnrichmentResult, Field, Method

PROGRESS_STEPS = [
    "Discovering pages",
    "Crawling website",
    "Extracting company information",
    "Extracting contacts",
    "Detecting technologies",
    "Detecting signals",
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


class WebsiteIntelligencePipeline:
    def __init__(self, website: str, max_pages: int = 10, max_depth: int = 2,
                 progress=None):
        self.website = _normalize_website(website)
        self.max_pages = max_pages
        self.max_depth = max_depth
        self._progress = progress

    def _emit(self, step_index: int, message: str = ""):
        if self._progress:
            try:
                self._progress(step_index, message or PROGRESS_STEPS[step_index])
            except Exception:
                # Progress reporting must never break enrichment.
                pass

    def run(self) -> EnrichmentResult:
        result = EnrichmentResult(website=self.website)
        session = build_session()
        try:
            # 1 + 2. Discover + crawl (BFS does both; we report them together).
            self._emit(0)
            crawled = discover_relevant_pages(
                self.website, session=session,
                max_pages=self.max_pages, max_depth=self.max_depth,
                progress=lambda msg: self._emit(1, msg),
            )
            pages = [page for page, _soup in crawled]
            soups_by_url = {page.url: soup for page, soup in crawled}
            result.pages_crawled = [
                {"url": p.url, "status": p.status_code,
                 "error": p.error} for p in pages
            ]
            result.errors = [
                {"url": p.url, "error": p.error} for p in pages if p.error
            ]

            # If the homepage is blocked / unreachable, stop here with a clear reason
            # rather than extracting junk (e.g. an "Access Denied" page title would
            # otherwise become the company name).
            reason = extractors.diagnose_readability(pages)
            if reason in ("blocked", "unreachable"):
                result.notes.append(extractors.READABILITY_MESSAGES[reason])
                self._emit(8)
                return result
            # A JavaScript-rendered ("empty") body has no readable content, but the
            # <head> usually still carries server-rendered og/meta/title/favicon (for
            # SEO/social). Note the limitation but fall through to harvest those —
            # partial enrichment from metadata beats returning nothing.
            if reason == "empty":
                result.notes.append(extractors.READABILITY_MESSAGES["empty"])

            homepage = pages[0]
            home_soup = soups_by_url.get(homepage.url)

            # 3. Company information (each field already carries provenance).
            self._emit(2)
            company = (extractors.extract_company_info(homepage, home_soup)
                       if home_soup else {})
            result.company_name = company.get("company_name") or Field()
            result.logo = company.get("logo") or Field()
            # Prefer Wikipedia's neutral third-person summary when we can confirm the
            # match by domain (see wikipedia.py); otherwise a real company description
            # (JSON-LD / About page) over the homepage's marketing og:description.
            result.description = (extractors.select_description(pages, soups_by_url)
                                  or company.get("description") or Field())
            wiki_text, wiki_src = wikipedia.fetch_company_description(
                result.company_name.value if result.company_name else "",
                self.website)
            if wiki_text:
                result.description = Field(wiki_text, wiki_src, Method.WIKIPEDIA)

            # 4. Contacts: emails, phones, social, team. (Addresses are
            #    intentionally skipped — too unreliable to be worth surfacing.)
            self._emit(3)
            result.emails = extractors.extract_emails(pages)
            result.phones = extractors.extract_phones(pages)
            result.social_profiles = extractors.extract_social_profiles(
                pages, soups_by_url, extra_links=company.get("social_links"))
            result.contacts = extractors.discover_team_members(pages, soups_by_url)
            result.employees = extractors.estimate_employees(pages)

            # 5. Technologies.
            self._emit(4)
            result.technologies = extractors.detect_technologies(pages)

            # 6. Signals.
            self._emit(5)
            result.signals = extractors.detect_signals(pages)

            # 7. Industry (aggregate classifier over all crawled pages).
            self._emit(6)
            industry, confidence = extractors.classify_industry(pages, company)
            result.industry = Field(industry, self.website, Method.KEYWORD_CLASSIFIER) \
                if industry else Field()
            result.industry_confidence = confidence

            # 8 + 9. Done (saving handled by caller).
            self._emit(7)
            self._emit(8)
            return result
        finally:
            session.close()


def enrich(website: str, max_pages: int = 10, max_depth: int = 2, progress=None):
    """Convenience wrapper returning the canonical result dict."""
    pipeline = WebsiteIntelligencePipeline(
        website, max_pages=max_pages, max_depth=max_depth, progress=progress)
    return pipeline.run()
