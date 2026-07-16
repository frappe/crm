# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Same-domain, depth-limited BFS crawler. Caps, priorities and skip-patterns
come from config (Settings child tables), not module constants.

Exposes:
    crawl()           -> ranked list of (CrawledPage, soup) tuples, homepage first
    crawl_page()      -> fetch + parse a single page into a CrawledPage
    extract_content() -> pull title/headings/visible text from soup
"""

from __future__ import annotations

import re
from collections import deque
from functools import lru_cache
from urllib.parse import urldefrag, urljoin, urlparse
from urllib.robotparser import RobotFileParser
from xml.etree import ElementTree as ET

import tldextract
from bs4 import BeautifulSoup

from .http import build_session, fetch
from .result import CrawledPage

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
	"""Query strings are dropped, not canonicalized -- almost always tracking
	noise, not a distinct page identity, for the pages this crawler cares about."""
	url, _frag = urldefrag(url)
	parsed = urlparse(url)
	if parsed.query:
		url = parsed._replace(query="").geturl()
	if url.endswith("/") and len(urlparse(url).path) > 1:
		url = url.rstrip("/")
	return url


@lru_cache(maxsize=1)
def _tld_extractor() -> tldextract.TLDExtract:
	"""Pinned to the bundled PSL snapshot (no network fetch); private suffixes like
	``github.io``/``vercel.app`` stay registrable so distinct tenants count as distinct sites."""
	return tldextract.TLDExtract(
		suffix_list_urls=(),
		cache_dir=None,
		include_psl_private_domains=True,
	)


def registrable_domain(netloc: str) -> str:
	"""``www.acme.co.uk`` -> ``acme.co.uk`` -- avoids a naive last-two-labels rule
	collapsing all of ``*.co.uk`` into one same-site bucket."""
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
	"""Lower number = crawl sooner. Matches the leaf path segment only -- an
	ancestor match alone (e.g. a news article under "/about-us/...") must not
	inherit that segment's priority."""
	path = urlparse(url).path.rstrip("/")
	leaf = path.rsplit("/", 1)[-1] if path else ""
	haystack = (leaf + " " + (anchor_text or "")).lower()
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
			# Malformed regex: fall back to substring match.
			if pat.lower() in low:
				return False
	return True


def extract_content(soup: BeautifulSoup) -> dict:
	"""Mutates ``soup`` (decomposes script/style) -- pass a throwaway copy if the
	caller needs the original DOM afterwards."""
	title = ""
	if soup.title and soup.title.string:
		title = soup.title.string.strip()

	headings = []
	for tag in soup.find_all(["h1", "h2", "h3"]):
		txt = tag.get_text(" ", strip=True)
		if txt:
			headings.append(txt)

	for node in soup(["script", "style", "noscript", "template", "svg"]):
		node.decompose()
	text = soup.get_text(" ", strip=True)
	text = " ".join(text.split())

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
	"""``extract_content`` runs on a throwaway parse so the returned soup stays unmutated."""
	soup = BeautifulSoup(html, "html.parser")
	content = extract_content(BeautifulSoup(html, "html.parser"))
	page.title = content["title"]
	page.headings = content["headings"]
	page.text = content["text"]
	return soup


def crawl_page(url, cfg, session=None):
	"""Returns (CrawledPage, soup_or_None); failures land on ``CrawledPage.error``
	instead of raising."""
	status, html, error, final_url = fetch(url, cfg, session=session)
	# Resolved URL: links and provenance match the host that actually served the body.
	page = CrawledPage(url=final_url or url, status_code=status, html=html or "", error=error)
	soup = _parse_and_fill(page, html) if (html and not error) else None
	return page, soup


ABOUT_PROBE_PATHS = ("/about", "/about-us", "/company", "/our-story")
ABOUT_MIN_TEXT = 200


def load_robots(start_url, cfg, session=None):
	"""Returns ``None`` when absent/unreadable (convention: allow all). Never raises
	-- robots is advisory and must not break enrichment."""
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
	"""True if robots is absent or permits ``url`` for ``user_agent``; fails open."""
	if robots is None:
		return True
	try:
		return robots.can_fetch(user_agent or "*", url)
	except Exception:
		return True


def probe_about_pages(home_url, cfg, session=None, skip_urls=()):
	"""Returns ``[(CrawledPage, soup)]`` for the first readable hit among
	``ABOUT_PROBE_PATHS`` not already crawled, else ``[]``."""
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


# --------------------------------------------------------------------------- #
# Sitemap discovery
# --------------------------------------------------------------------------- #
# Additive on top of link-following BFS: seeds pages the sitemap author flagged.
# No sitemap, or an unreadable one, falls through to plain link-following, silently.
SITEMAP_MAX_SITEMAPS = 5  # sitemap files fetched; guards pathological sitemap indexes
SITEMAP_MAX_URLS = 200  # total <loc> entries collected across all fetched sitemaps


def _local_tag(tag: str) -> str:
	"""Strip the XML namespace off a tag: '{http://.../0.9}urlset' -> 'urlset'."""
	return tag.rsplit("}", 1)[-1] if tag else tag


def _parse_sitemap(xml_text: str):
	"""Returns ('urlset' | 'sitemapindex' | None, [loc, ...]); never raises.

	Rejects any DOCTYPE before parsing as an XML entity-expansion guard -- a
	legitimate sitemap never has one.
	"""
	if "<!doctype" in xml_text.lower():
		return None, []
	try:
		root = ET.fromstring(xml_text)
	except ET.ParseError:
		return None, []
	kind = _local_tag(root.tag)
	if kind not in ("urlset", "sitemapindex"):
		return None, []
	child_tag = "sitemap" if kind == "sitemapindex" else "url"
	locs = []
	for el in root:
		if _local_tag(el.tag) != child_tag:
			continue
		for child in el:
			if _local_tag(child.tag) == "loc" and child.text:
				locs.append(child.text.strip())
				break
	return kind, locs


def discover_sitemap_urls(start_url, cfg, session, robots):
	"""robots.txt ``Sitemap:`` first, else ``/sitemap.xml``. Follows one level of
	``<sitemapindex>`` nesting, bounded by ``SITEMAP_MAX_SITEMAPS``/``SITEMAP_MAX_URLS``.
	Never raises -- any failure returns ``[]`` and falls through to plain BFS."""
	try:
		parsed = urlparse(normalize_url(start_url))
		if not parsed.netloc:
			return []

		candidates = []
		if robots is not None:
			try:
				candidates.extend(robots.site_maps() or [])
			except Exception:
				pass
		if not candidates:
			candidates.append(f"{parsed.scheme}://{parsed.netloc}/sitemap.xml")

		to_fetch = deque(candidates[:SITEMAP_MAX_SITEMAPS])
		sitemaps_queued = len(to_fetch)  # running total: seed + discovered children
		fetched_sitemaps = set()
		urls = []
		seen_urls = set()

		while to_fetch and len(fetched_sitemaps) < SITEMAP_MAX_SITEMAPS and len(urls) < SITEMAP_MAX_URLS:
			sitemap_url = to_fetch.popleft()
			if sitemap_url in fetched_sitemaps:
				continue
			fetched_sitemaps.add(sitemap_url)
			if not same_site(sitemap_url, parsed.netloc):
				continue

			status, body, error, _final = fetch(sitemap_url, cfg, session=session, html_only=False)
			if error or status != 200 or not body:
				continue

			kind, locs = _parse_sitemap(body)

			if kind == "sitemapindex":
				for loc in locs:
					if sitemaps_queued >= SITEMAP_MAX_SITEMAPS:
						break
					to_fetch.append(loc)
					sitemaps_queued += 1

			elif kind == "urlset":
				for loc in locs:
					norm = normalize_url(loc)
					if norm in seen_urls:
						continue
					seen_urls.add(norm)
					urls.append(norm)
					if len(urls) >= SITEMAP_MAX_URLS:
						break

		return urls
	except Exception:
		return []


def crawl(start_url, cfg, session=None, progress=None):
	"""Breadth-first crawl prioritizing company-info pages. Caps, link-priority and
	skip patterns come from ``cfg``. ``progress`` is an optional ``fn(message)`` callback."""
	max_pages = int(cfg.setting("max_pages"))
	max_depth = int(cfg.setting("max_depth"))
	link_priority = cfg.link_priority
	skip_patterns = cfg.skip_patterns

	user_agent = cfg.setting("user_agent")
	own_session = session is None
	session = session or build_session(cfg)
	start_url = normalize_url(start_url)
	base_netloc = urlparse(start_url).netloc

	# robots.txt only gates discovered links; skip the fetch for homepage-only runs.
	crawl_beyond_homepage = max_depth >= 1 and max_pages > 1
	robots = load_robots(start_url, cfg, session) if crawl_beyond_homepage else None

	visited = set()
	# Resolved (post-redirect) URLs already crawled -- catches a duplicate the
	# pre-fetch `visited` check can't (e.g. /contact.html -> /contact).
	visited_resolved = set()
	results = []
	# Queue holds (url, depth, anchor_text).
	queue = deque([(start_url, 0, "")])

	# Sitemap-seeded links join at depth 1, never 0, so the homepage still wins
	# the first pop. Additive only -- a site with no sitemap is unaffected.
	if crawl_beyond_homepage and cfg.setting("use_sitemap", True):
		queued_from_sitemap = set()
		for loc in discover_sitemap_urls(start_url, cfg, session, robots):
			link = normalize_url(loc)
			if link == start_url or link in queued_from_sitemap:
				continue
			if not same_site(link, base_netloc) or not _is_crawlable(link, skip_patterns):
				continue
			if not _robots_allows(robots, user_agent, link):
				continue
			queued_from_sitemap.add(link)
			queue.append((link, 1, ""))

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
			resolved = normalize_url(page.url) if page.url else ""

			if not results:
				# Homepage: can't be a duplicate yet. Adopt its resolved host as the
				# same-site base if it redirected elsewhere.
				if resolved:
					base_netloc = urlparse(page.url).netloc or base_netloc
			else:
				# A redirect can land here under a different requested URL (e.g.
				# /contact.html -> /contact) -- drop the duplicate, no budget spent.
				if resolved and resolved in visited_resolved:
					continue
				if soup is not None and page.url and not same_site(page.url, base_netloc):
					# Same-site link redirected off-domain; fetch() only checks SSRF
					# per hop, not same-site scope. Clear every parsed field (not just
					# html/text) so nothing -- including title/headings, already
					# filled in by crawl_page() -- leaks into extraction.
					page.error = page.error or f"redirected off-site to {urlparse(page.url).netloc}"
					page.html = ""
					page.text = ""
					page.title = ""
					page.headings = []
					soup = None

			if resolved:
				visited_resolved.add(resolved)

			results.append((page, soup))

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
