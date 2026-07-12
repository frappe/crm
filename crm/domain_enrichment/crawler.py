# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Same-domain, depth-limited BFS crawler. Caps, priorities and skip-patterns
come from config (Settings child tables), not module constants.

Exposes:

    crawl()             -> ranked list of (CrawledPage, soup) tuples, homepage first
    crawl_page()        -> fetch + parse a single page into a CrawledPage
    extract_content()   -> pull title/headings/visible text from soup

Same registrable domain only; respects the page cap, depth cap, and skip patterns.
"""

from __future__ import annotations

import re
from collections import deque
from functools import lru_cache
from urllib.parse import urldefrag, urljoin, urlparse
from urllib.robotparser import RobotFileParser

import tldextract
from bs4 import BeautifulSoup

from .http import build_session, fetch
from .result import CrawledPage

# Asset / non-HTML extensions we never want to crawl (mechanics, not knowledge).
SKIP_EXTENSIONS = (
	".pdf",
	".jpg",
	".jpeg",
	".png",
	".gif",
	".svg",
	".webp",
	".ico",
	".css",
	".js",
	".zip",
	".gz",
	".mp4",
	".mp3",
	".avi",
	".woff",
	".woff2",
	".ttf",
	".eot",
	".xml",
	".json",
	".rss",
)
SKIP_SCHEMES = ("mailto:", "tel:", "javascript:", "data:", "#")


def normalize_url(url: str) -> str:
	"""Strip fragments and trailing slashes for stable dedupe."""
	url, _frag = urldefrag(url)
	if url.endswith("/") and len(urlparse(url).path) > 1:
		url = url.rstrip("/")
	return url


@lru_cache(maxsize=1)
def _tld_extractor() -> tldextract.TLDExtract:
	"""Public Suffix List backed extractor, built once and cached.

	``suffix_list_urls=()`` + ``cache_dir=None`` pin it to the snapshot bundled
	with tldextract -- it never fetches the PSL over the network (deterministic,
	offline, no surprise latency on first crawl). ``include_psl_private_domains``
	makes hosting suffixes like ``github.io`` / ``vercel.app`` registrable, so two
	tenants under one of them count as different sites for scoping.
	"""
	return tldextract.TLDExtract(
		suffix_list_urls=(),
		cache_dir=None,
		include_psl_private_domains=True,
	)


def registrable_domain(netloc: str) -> str:
	"""The registrable domain of ``netloc`` per the Public Suffix List.

	``www.acme.co.uk`` -> ``acme.co.uk``; ``blog.acme.com`` -> ``acme.com``. This
	is the same-site key: a naive last-two-labels rule collapses every ``*.co.uk``
	(or ``*.github.io``) to one bucket, so the crawler would wander into unrelated
	third-party sites sharing a public suffix. Hosts with no registrable suffix
	(bare hostnames, IPs, ``localhost``) fall back to the host itself.
	"""
	netloc = netloc.lower().split(":")[0]
	extracted = _tld_extractor()(netloc)
	if extracted.domain and extracted.suffix:
		return f"{extracted.domain}.{extracted.suffix}"
	return extracted.domain or netloc


def same_site(url: str, base_netloc: str) -> bool:
	try:
		return registrable_domain(urlparse(url).netloc) == registrable_domain(base_netloc)
	except Exception:
		return False


def _link_priority(url: str, anchor_text: str, link_priority: list) -> float:
	"""Lower number = crawl sooner. Matching links score by their keyword's rank,
	weighted; non-matching pages sort last. ``link_priority`` is a list of
	(keyword, weight) tuples from config."""
	haystack = (urlparse(url).path + " " + (anchor_text or "")).lower()
	best = None
	for idx, (kw, weight) in enumerate(link_priority):
		if kw and kw in haystack:
			# Higher weight -> earlier; ties broken by config order.
			score = idx - (weight or 1.0)
			if best is None or score < best:
				best = score
	return best if best is not None else len(link_priority) + 1


def _is_crawlable(url: str, skip_patterns: list) -> bool:
	low = url.lower()
	if any(low.startswith(s) for s in SKIP_SCHEMES):
		return False
	path = urlparse(url).path.lower()
	if path.endswith(SKIP_EXTENSIONS):
		return False
	if urlparse(url).scheme not in ("http", "https"):
		return False
	for pat in skip_patterns:
		try:
			if re.search(pat, url, re.IGNORECASE):
				return False
		except re.error:
			# Treat a malformed admin skip-pattern as a plain substring.
			if pat.lower() in low:
				return False
	return True


def extract_content(soup: BeautifulSoup) -> dict:
	"""Pull title, headings and clean visible text out of a parsed page.

	NOTE: this mutates ``soup`` (it decomposes script/style nodes), so callers
	that need the original DOM afterwards must pass a throwaway copy.
	"""
	title = ""
	if soup.title and soup.title.string:
		title = soup.title.string.strip()

	headings = []
	for tag in soup.find_all(["h1", "h2", "h3"]):
		txt = tag.get_text(" ", strip=True)
		if txt:
			headings.append(txt)

	# Remove non-content nodes before grabbing text.
	for node in soup(["script", "style", "noscript", "template", "svg"]):
		node.decompose()
	text = soup.get_text(" ", strip=True)
	text = " ".join(text.split())  # collapse runaway whitespace

	return {"title": title, "headings": headings, "text": text}


def _links_on_page(soup, page_url, base_netloc, skip_patterns):
	"""Yield (normalized_url, anchor_text) for same-site, crawlable links."""
	for a in soup.find_all("a", href=True):
		href = a["href"].strip()
		if not href or any(href.lower().startswith(s) for s in SKIP_SCHEMES):
			continue
		absolute = normalize_url(urljoin(page_url, href))
		if not _is_crawlable(absolute, skip_patterns):
			continue
		if not same_site(absolute, base_netloc):
			continue
		yield absolute, a.get_text(" ", strip=True)


def _parse_and_fill(page, html):
	"""Parse ``html``, fill ``page`` title/headings/text, and return a fresh soup.

	``extract_content`` mutates its soup (decomposes script/style), so it runs on a
	throwaway parse while the returned soup stays unmutated for the caller.
	"""
	soup = BeautifulSoup(html, "html.parser")
	content = extract_content(BeautifulSoup(html, "html.parser"))
	page.title = content["title"]
	page.headings = content["headings"]
	page.text = content["text"]
	return soup


def crawl_page(url, cfg, session=None):
	"""Fetch and parse a single page. Returns (CrawledPage, soup_or_None).

	Failures are captured on ``CrawledPage.error`` rather than raised. The soup
	returned is a fresh, unmutated parse (``extract_content`` runs on a copy).
	"""
	status, html, error, final_url = fetch(url, cfg, session=session)
	# Use the post-redirect URL so relative links resolve and provenance is recorded
	# against the host that actually served the body.
	page = CrawledPage(url=final_url or url, status_code=status, html=html or "", error=error)
	soup = _parse_and_fill(page, html) if (html and not error) else None
	return page, soup


# Common About-page paths probed when the BFS didn't surface one (some sites don't
# link About prominently, but it's the best source of a company description).
ABOUT_PROBE_PATHS = ("/about", "/about-us", "/company", "/our-story")
# A probed page needs at least this much readable text to be worth keeping.
ABOUT_MIN_TEXT = 200


def load_robots(start_url, cfg, session=None):
	"""Fetch and parse the site's ``robots.txt`` via the SSRF-guarded fetcher.

	Returns a populated ``RobotFileParser``, or ``None`` when robots.txt is absent or
	unreadable (per convention: allow all). Uses ``fetch(..., html_only=False)`` so the
	``text/plain`` body isn't skipped, and never raises -- robots is advisory here and
	must not break enrichment.
	"""
	try:
		parsed = urlparse(normalize_url(start_url))
		if not parsed.netloc:
			return None
		robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
		own = session is None
		session = session or build_session(cfg)
		try:
			status, body, error, _final = fetch(robots_url, cfg, session=session, html_only=False)
		finally:
			if own:
				session.close()
		if error or status != 200 or not body:
			return None
		rp = RobotFileParser()
		rp.parse(body.splitlines())
		return rp
	except Exception:
		return None


def _robots_allows(robots, user_agent, url):
	"""True if robots is absent or permits fetching ``url`` for ``user_agent``. A
	malformed robots quirk never blocks enrichment (fails open)."""
	if robots is None:
		return True
	try:
		return robots.can_fetch(user_agent or "*", url)
	except Exception:
		return True


def probe_about_pages(home_url, cfg, session=None, skip_urls=()):
	"""Best-effort fetch of common About-page paths not already crawled.

	Returns ``[(CrawledPage, soup)]`` for the first probed path that returns a readable
	page (or empty). SSRF + byte caps are enforced by ``fetch``; failures are ignored.
	Bounded: stops at the first readable hit, at most ``len(ABOUT_PROBE_PATHS)`` fetches.
	"""
	skip = {normalize_url(u) for u in skip_urls}
	user_agent = cfg.setting("user_agent")
	own_session = session is None
	session = session or build_session(cfg)
	robots = load_robots(home_url, cfg, session)
	try:
		for path in ABOUT_PROBE_PATHS:
			url = normalize_url(urljoin(home_url, path))
			if url in skip:
				continue
			skip.add(url)
			if not _robots_allows(robots, user_agent, url):
				continue
			page, soup = crawl_page(url, cfg, session=session)
			if (
				soup is not None
				and page.status_code == 200
				and not page.error
				and len(page.text) >= ABOUT_MIN_TEXT
			):
				return [(page, soup)]
	finally:
		if own_session:
			session.close()
	return []


def crawl(start_url, cfg, session=None, progress=None):
	"""Breadth-first crawl from ``start_url``, prioritizing company-info pages.

	Caps (``max_pages``/``max_depth``), link-priority order and skip patterns all
	come from ``cfg``. Returns a list of (CrawledPage, soup) tuples, homepage
	first. Respects the page cap, depth cap, and same-domain rule.

	``progress`` is an optional ``fn(message)`` called per crawled URL.
	"""
	max_pages = int(cfg.setting("max_pages"))
	max_depth = int(cfg.setting("max_depth"))
	link_priority = cfg.link_priority
	skip_patterns = cfg.skip_patterns

	user_agent = cfg.setting("user_agent")
	own_session = session is None
	session = session or build_session(cfg)
	start_url = normalize_url(start_url)
	base_netloc = urlparse(start_url).netloc

	# Respect robots.txt for discovered links -- but only when we actually crawl beyond
	# the homepage (skip the extra fetch for homepage-only / preview runs, which follow
	# no links). The explicit start URL is always fetched; robots gates discovery.
	robots = load_robots(start_url, cfg, session) if (max_depth >= 1 and max_pages > 1) else None

	visited = set()
	results = []
	# Queue holds (url, depth, anchor_text). We pop the highest-priority item.
	queue = deque([(start_url, 0, "")])

	try:
		while queue and len(results) < max_pages:
			# Pick the highest-priority queued URL (homepage first, then by keyword).
			queue = deque(
				sorted(
					queue,
					key=lambda item: (
						0 if item[1] == 0 else 1,
						_link_priority(item[0], item[2], link_priority),
					),
				)
			)
			url, depth, _anchor = queue.popleft()
			url = normalize_url(url)
			if url in visited:
				continue
			visited.add(url)

			if progress:
				progress(f"Crawling {url}")
			page, soup = crawl_page(url, cfg, session=session)
			results.append((page, soup))

			# If the homepage redirected to another host, adopt the resolved domain as
			# the same-site base so the rest of the crawl follows the real site.
			if len(results) == 1:
				resolved_netloc = urlparse(page.url).netloc
				if resolved_netloc:
					base_netloc = resolved_netloc

			if soup is None or depth >= max_depth:
				continue

			# Resolve links against the page's resolved URL, not the requested one.
			seen_here = set()
			for link, anchor in _links_on_page(soup, page.url, base_netloc, skip_patterns):
				if link in visited or link in seen_here:
					continue
				if not _robots_allows(robots, user_agent, link):
					continue
				seen_here.add(link)
				queue.append((link, depth + 1, anchor))
	finally:
		if own_session:
			session.close()

	return results
