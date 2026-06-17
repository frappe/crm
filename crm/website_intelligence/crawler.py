"""Same-domain, depth-limited crawler.

Implements the three functions the spec calls out explicitly:

    discover_relevant_pages()  -> ranked list of internal URLs to visit
    crawl_page()               -> fetch + parse a single page into a CrawledPage
    extract_content()          -> pull title/headings/visible text from soup

Constraints (hard caps): max 10 pages, max depth 2, same registrable domain only.
Pages whose path/anchor text hints at company info are prioritized.
"""

from __future__ import annotations

from collections import deque
from urllib.parse import urljoin, urlparse, urldefrag

from bs4 import BeautifulSoup

from .http_client import build_session, fetch
from .models import CrawledPage

MAX_PAGES = 10
MAX_DEPTH = 2

# Path/anchor keywords that mark a page as worth crawling, highest priority first.
PRIORITY_KEYWORDS = [
    "about", "contact", "team", "leadership", "careers",
    "company", "people", "founders", "management", "jobs",
]

# Things we never want to crawl.
SKIP_EXTENSIONS = (
    ".pdf", ".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp", ".ico",
    ".css", ".js", ".zip", ".gz", ".mp4", ".mp3", ".avi", ".woff",
    ".woff2", ".ttf", ".eot", ".xml", ".json", ".rss",
)
SKIP_SCHEMES = ("mailto:", "tel:", "javascript:", "data:", "#")


def normalize_url(url: str) -> str:
    """Strip fragments and trailing slashes for stable dedupe."""
    url, _frag = urldefrag(url)
    if url.endswith("/") and len(urlparse(url).path) > 1:
        url = url.rstrip("/")
    return url


def registrable_domain(netloc: str) -> str:
    """A pragmatic same-site check: compare the last two labels (example.com),
    treating www as insignificant. Good enough for MVP scoping — we are not
    trying to follow links onto unrelated domains."""
    netloc = netloc.lower().split(":")[0]
    if netloc.startswith("www."):
        netloc = netloc[4:]
    parts = netloc.split(".")
    return ".".join(parts[-2:]) if len(parts) >= 2 else netloc


def same_site(url: str, base_netloc: str) -> bool:
    try:
        return registrable_domain(urlparse(url).netloc) == registrable_domain(base_netloc)
    except Exception:
        return False


def _link_priority(url: str, anchor_text: str) -> int:
    """Lower number = crawl sooner. Homepage-adjacent priority pages score 0."""
    haystack = (urlparse(url).path + " " + (anchor_text or "")).lower()
    for idx, kw in enumerate(PRIORITY_KEYWORDS):
        if kw in haystack:
            return idx
    return len(PRIORITY_KEYWORDS) + 1


def _is_crawlable(url: str) -> bool:
    if any(url.lower().startswith(s) for s in SKIP_SCHEMES):
        return False
    path = urlparse(url).path.lower()
    if path.endswith(SKIP_EXTENSIONS):
        return False
    return urlparse(url).scheme in ("http", "https")


def extract_content(soup: BeautifulSoup) -> dict:
    """Pull title, headings and clean visible text out of a parsed page."""
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
    # Collapse runaway whitespace.
    text = " ".join(text.split())

    return {"title": title, "headings": headings, "text": text}


def _links_on_page(soup: BeautifulSoup, page_url: str, base_netloc: str):
    """Yield (normalized_url, anchor_text) for same-site, crawlable links."""
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if not href or any(href.lower().startswith(s) for s in SKIP_SCHEMES):
            continue
        absolute = normalize_url(urljoin(page_url, href))
        if not _is_crawlable(absolute):
            continue
        if not same_site(absolute, base_netloc):
            continue
        yield absolute, a.get_text(" ", strip=True)


def crawl_page(url: str, session=None) -> tuple[CrawledPage, BeautifulSoup | None]:
    """Fetch and parse a single page. Returns (CrawledPage, soup_or_None).

    Failures are captured on the CrawledPage.error field rather than raised.
    """
    status, html, error = fetch(url, session=session)
    page = CrawledPage(url=url, status_code=status, html=html or "", error=error)
    if error or not html:
        return page, None

    soup = BeautifulSoup(html, "html.parser")
    content = extract_content(BeautifulSoup(html, "html.parser"))  # fresh soup; extract_content mutates
    page.title = content["title"]
    page.headings = content["headings"]
    page.text = content["text"]
    return page, soup


def discover_relevant_pages(start_url: str, session=None,
                            max_pages: int = MAX_PAGES,
                            max_depth: int = MAX_DEPTH,
                            progress=None):
    """Breadth-first crawl from `start_url`, prioritizing company-info pages.

    Returns a list of (CrawledPage, soup) tuples, homepage first. Respects the
    page cap, depth cap, and same-domain rule.
    """
    own_session = session is None
    session = session or build_session()
    start_url = normalize_url(start_url)
    base_netloc = urlparse(start_url).netloc

    visited = set()
    results = []
    # Queue holds (url, depth, anchor_text). We pop the highest-priority item.
    queue = deque([(start_url, 0, "")])

    try:
        while queue and len(results) < max_pages:
            # Pick the highest-priority queued URL (stable, deterministic).
            queue = deque(sorted(queue, key=lambda item: (item[1] == 0 and -1 or 0,
                                                           _link_priority(item[0], item[2]))))
            url, depth, _anchor = queue.popleft()
            url = normalize_url(url)
            if url in visited:
                continue
            visited.add(url)

            if progress:
                progress(f"Crawling {url}")
            page, soup = crawl_page(url, session=session)
            results.append((page, soup))

            if soup is None or depth >= max_depth:
                continue

            # Enqueue child links we have not seen, de-duplicated.
            seen_here = set()
            for link, anchor in _links_on_page(soup, url, base_netloc):
                if link in visited or link in seen_here:
                    continue
                seen_here.add(link)
                queue.append((link, depth + 1, anchor))
    finally:
        if own_session:
            session.close()

    return results
