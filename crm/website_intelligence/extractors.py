## TODO: This file is getting long and messy. Consider splitting into multiple files or extracting everything into a doctype field

"""Deterministic, rule-based extractors.

Each extractor takes parsed pages and returns structured evidence with source
URLs. No external services, no ML — only JSON-LD, meta tags, regex and curated
keyword/signature tables.
"""

from __future__ import annotations

import json
import re
from urllib.parse import urljoin, urlparse

from .models import (
    Address, Contact, Email, Field, Method, Phone, Signals, SocialProfile,
    Technology,
)

# --------------------------------------------------------------------------- #
# Regexes
# --------------------------------------------------------------------------- #
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")

# International-ish phone numbers: optional +, country/area groups, separators.
PHONE_RE = re.compile(
    r"""(?<!\w)
    (\+?\d{1,3}[\s.-]?)?      # optional country code
    (\(?\d{2,4}\)?[\s.-]?)    # area / first group
    \d{3,4}[\s.-]?\d{3,4}     # subscriber number
    (?!\w)""",
    re.VERBOSE,
)

# Emails that are almost always noise (asset hashes, example domains, images).
EMAIL_BLOCKLIST_SUBSTR = ("example.com", "sentry.io", "@2x", "@3x", ".png", ".jpg",
                          ".gif", ".svg", ".webp", "your-email", "email@")

# Social network signatures: network -> compiled host/path matcher.
SOCIAL_PATTERNS = {
    "linkedin": re.compile(r"linkedin\.com/(company|in|school)/", re.I),
    "twitter": re.compile(r"(twitter\.com|x\.com)/[A-Za-z0-9_]+", re.I),
    "github": re.compile(r"github\.com/[A-Za-z0-9_.-]+", re.I),
    "facebook": re.compile(r"facebook\.com/[A-Za-z0-9_.\-/]+", re.I),
    "instagram": re.compile(r"instagram\.com/[A-Za-z0-9_.]+", re.I),
    "youtube": re.compile(r"youtube\.com/(channel/|c/|user/|@)[A-Za-z0-9_.\-]+", re.I),
}
# Generic landing pages we should not treat as a profile.
SOCIAL_NEGATIVE = re.compile(
    r"/(sharer|share|intent|home|login|signup|privacy|tos)\b", re.I
)

# Technology signatures: tech name -> list of (substring, human evidence).
TECH_SIGNATURES = {
    "WordPress": ["wp-content", "wp-json", "wp-includes", 'content="WordPress'],
    "Shopify": ["cdn.shopify.com", "shopify.com", "x-shopify", "myshopify"],
    "Next.js": ["/_next/", "__NEXT_DATA__", "next/script"],
    "React": ["react.production.min.js", "react-dom", "data-reactroot", "__react"],
    "Vue.js": ["vue.runtime", "vue.min.js", "data-v-", "__vue__"],
    "Frappe": ["frappe", "desk.min.js", "frappe-web.bundle", "/assets/frappe/"],
    "HubSpot": ["hubspotutk", "hs-scripts.com", "js.hs-analytics", "hsforms.net"],
    "Google Analytics": ["www.googletagmanager.com/gtag", "google-analytics.com",
                          "gtag(", "ga('create'"],
    "Google Tag Manager": ["googletagmanager.com/gtm.js", "GTM-"],
    "Cloudflare": ["cdnjs.cloudflare.com", "__cf_bm", "cf-ray"],
    "Webflow": ["assets.website-files.com", "webflow.js", "data-wf-"],
    "Wix": ["static.wixstatic.com", "wix.com", "_wixCssAndJs"],
    "Squarespace": ["squarespace.com", "static1.squarespace"],
}

# Designations that mark a real leadership/team entry.
DESIGNATION_KEYWORDS = [
    "Chief Executive Officer", "Chief Technology Officer",
    "Chief Operating Officer", "Chief Financial Officer",
    "Chief Marketing Officer", "Chief Product Officer",
    "Co-Founder", "Cofounder", "Co Founder", "Founder",
    "CEO", "CTO", "COO", "CFO", "CMO", "CPO",
    "VP ", "Vice President", "President",
    "Director", "Head of", "Head ", "Lead ", "Manager",
]

# Business signal keyword tables.
SIGNAL_KEYWORDS = {
    "hiring": ["hiring", "careers", "open positions", "join our team",
               "we're hiring", "we are hiring", "open roles", "job openings"],
    "funding": ["funding", "raised", "investment", "seed round", "series a",
                "series b", "series c", "venture", "backed by", "investors"],
    "ai": ["ai powered", "ai-powered", "machine learning", "artificial intelligence",
           "generative ai", "deep learning", "neural network", "llm"],
}

# Industry classifier: industry -> weighted keyword table.
# Industry vocabulary. Keywords are intentionally specific (multi-word where
# possible) to avoid generic site copy ("brand", "growth", "marketing") matching
# everything. Matched with word boundaries against headline text only (see
# classify_industry), never footer/body, which is the main source of noise.
INDUSTRY_KEYWORDS = {
    "ERP": ["erp", "enterprise resource planning", "procurement",
            "supply chain management", "inventory management"],
    "CRM": ["crm", "customer relationship management", "sales pipeline",
            "lead management", "contact management"],
    "Ecommerce": ["ecommerce", "e-commerce", "online shopping", "online store",
                  "marketplace", "shopping cart", "add to cart", "add to bag",
                  "storefront", "checkout", "shop", "free shipping",
                  "free returns", "new arrivals", "best sellers", "bestsellers",
                  "size guide", "apparel", "clothing brand", "direct-to-consumer",
                  "quick commerce", "q-commerce", "online grocery", "online groceries",
                  "grocery delivery", "grocery app", "delivery app", "online shop"],
    "SaaS": ["saas", "software as a service", "subscription software",
             "cloud platform", "free trial"],
    "Technology": ["software", "developer", "developers", "api", "open source",
                   "cloud computing", "it services", "information technology",
                   "artificial intelligence", "machine learning"],
    "Semiconductors": ["semiconductor", "gpu", "graphics card", "processor",
                       "chipset", "supercomputer", "microprocessor"],
    "Manufacturing": ["manufacturing", "factory", "production line", "assembly line",
                      "fabrication", "industrial equipment", "3d printing",
                      "additive manufacturing", "cnc machining", "rapid prototyping",
                      "injection molding", "prototyping"],
    "Healthcare": ["healthcare", "health care", "clinic", "hospital", "patient care",
                   "medical", "telehealth", "pharmaceutical", "pharma"],
    "Education": ["education", "e-learning", "students", "curriculum", "university",
                  "online courses", "courses", "course", "edtech", "learning platform"],
    "Consulting": ["consulting", "advisory services", "consultants",
                   "professional services", "strategy consulting"],
    "Marketing": ["marketing agency", "digital marketing", "advertising agency",
                  "seo services", "ad campaigns", "media buying"],
    "Finance": ["fintech", "banking", "payments", "lending", "insurance",
                "financial services", "trading", "wealth management"],
    "Logistics": ["logistics", "freight", "warehousing", "fulfillment",
                  "shipping carrier", "last-mile delivery"],
    "Food & Beverage": ["food and beverage", "beverage", "beverages", "snacks",
                        "snack", "packaged food", "fmcg", "consumer goods",
                        "sparkling water", "iced tea", "energy drink", "soft drink",
                        "drink", "drinks", "soda", "kombucha", "cereal", "coffee",
                        "chocolate", "protein bar"],
    "Retail": ["retailer", "department store", "brick and mortar"],
    "Media": ["entertainment", "streaming service", "video game", "game studio",
              "publishing house", "news media", "broadcasting", "journalism",
              "journalists", "media company", "newsroom", "newsletter",
              "reported articles", "investigative", "editorial", "magazine",
              "podcast", "reporting on"],
    "Real Estate": ["real estate", "property management", "commercial property",
                    "interior design", "home design", "home improvement",
                    "remodeling", "decorating", "home renovation"],
    "Travel": ["hospitality", "tourism", "flight booking", "travel agency"],
    "Automotive": ["automotive", "electric vehicle", "car manufacturer"],
    "Telecom": ["telecommunications", "broadband", "network operator"],
    "Energy": ["renewable energy", "solar power", "oil and gas"],
    "Legal": ["law firm", "legal services", "litigation", "legal help",
              "legal documents", "legal advice", "attorney", "attorneys",
              "lawyer", "lawyers"],
    "Nonprofit": ["nonprofit", "non-profit", "ngo", "charity"],
}

# Don't guess when the signal is weak — leave the field blank instead.
INDUSTRY_MIN_SCORE = 2          # at least one headline/heading keyword hit
INDUSTRY_MIN_CONFIDENCE = 0.34  # the winner must clearly lead


# --------------------------------------------------------------------------- #
# JSON-LD
# --------------------------------------------------------------------------- #
def parse_json_ld(soup):
    """Return a flat list of JSON-LD dicts found on the page (handles @graph)."""
    blocks = []
    for tag in soup.find_all("script", attrs={"type": "application/ld+json"}):
        raw = tag.string or tag.get_text() or ""
        if not raw.strip():
            continue
        try:
            data = json.loads(raw)
        except (ValueError, TypeError):
            # Some sites emit slightly broken JSON-LD; skip rather than crash.
            continue
        if isinstance(data, dict):
            if "@graph" in data and isinstance(data["@graph"], list):
                blocks.extend([d for d in data["@graph"] if isinstance(d, dict)])
            else:
                blocks.append(data)
        elif isinstance(data, list):
            blocks.extend([d for d in data if isinstance(d, dict)])
    return blocks


# --------------------------------------------------------------------------- #
# Readability diagnosis — explain why a site yielded nothing
# --------------------------------------------------------------------------- #
# Markers of a bot-protection / WAF challenge page served instead of content.
WAF_MARKERS = (
    "_incapsula_resource", "incapsula", "captcha", "cf-browser-verification",
    "just a moment", "attention required", "access denied", "ddos protection",
    "please enable javascript", "enable cookies to continue", "are you a human",
)

READABILITY_MESSAGES = {
    "unreachable": "Couldn't reach this website (it timed out or refused the connection).",
    "blocked": "This website is behind bot protection, so its content can't be read. "
               "Try the company's corporate domain (e.g. acme.com vs shop.acme.com).",
    "empty": "This site's main content is JavaScript-rendered; only page metadata "
             "(title/description/logo) could be read, so some fields may be blank.",
}


def diagnose_readability(pages):
    """Judge the homepage: '' (readable), 'blocked', 'empty', or 'unreachable'.

    Company identity comes from the homepage, so we diagnose it specifically:
    an HTTP 401/403/429 or a WAF challenge means bot protection ('blocked');
    a 5xx/timeout/connection error means 'unreachable'; a 2xx page with almost
    no text is a JavaScript-only shell ('empty'). This lets us give a real reason
    instead of, say, reading "Access Denied" as the company name.
    """
    if not pages:
        return "unreachable"
    home = pages[0]
    if home.error or not home.status_code:
        return "unreachable"
    if home.status_code in (401, 403, 429):
        return "blocked"
    if home.status_code >= 500:
        return "unreachable"
    blob = (home.html or "")[:5000].lower()
    if any(marker in blob for marker in WAF_MARKERS):
        return "blocked"
    if len(home.text or "") < 200:
        return "empty"
    return ""


def _ld_type_matches(block, wanted):
    t = block.get("@type", "")
    types = t if isinstance(t, list) else [t]
    return any(str(x).lower() in wanted for x in types)


# --------------------------------------------------------------------------- #
# Company information
# --------------------------------------------------------------------------- #
def _meta_with_method(soup, *names):
    """Return (content, matched_name) for the first present meta tag."""
    for name in names:
        tag = (soup.find("meta", attrs={"property": name})
               or soup.find("meta", attrs={"name": name}))
        if tag and tag.get("content"):
            return tag["content"].strip(), name
    return "", ""


# A company name is usually the first chunk of a page <title>, before a
# separator that introduces a tagline (e.g. "PostHog – We make dev tools").
_NAME_SPLIT_RE = re.compile(r"\s*\|\s*|\s+[-–—•·]\s+|\s*:\s")
# Verbs/words that start a tagline sentence after the name
# (e.g. "ITC Ltd has diversified presence …" -> "ITC Ltd").
_NAME_TAGLINE_RE = re.compile(
    r"\s+(?:has|have|is|are|was|were|offers?|provides?|delivers?|helps?|"
    r"enables?|builds?|makes?|creates?|specializes?|brings?|"
    r"empowers?|powers?|leads?|connects?)\b", re.I)
_NAME_MAX_WORDS = 6


def _domain_brand(url):
    """The brand token from a URL's registrable domain, e.g. "8848digital" from
    "https://www.8848digital.com/" or "acme" from "https://shop.acme.com"."""
    netloc = (urlparse(url or "").netloc or "").lower().split(":")[0]
    if netloc.startswith("www."):
        netloc = netloc[4:]
    labels = [l for l in netloc.split(".") if l]
    return labels[-2] if len(labels) >= 2 else (labels[0] if labels else "")


def _compact(text):
    return re.sub(r"[^a-z0-9]", "", (text or "").lower())


def _clean_company_name(raw, site_url=""):
    """Trim a page title / og:title down to just the company name.

    Splits on tagline separators. Normally the brand is the first chunk, but some
    titles are "Tagline | Brand" (e.g. "Innovative IT Services | 8848 Digital"), so
    when a `site_url` is given we prefer the chunk that matches its domain brand. If
    the result is still a long sentence (a keyword-stuffed or descriptive og:title),
    cut it at the first tagline verb, then the first comma, then cap the length — so
    an Organization is never named with a whole sentence.
    """
    raw = (raw or "").strip()
    if not raw:
        return ""
    chunks = [c.strip() for c in _NAME_SPLIT_RE.split(raw) if c.strip()]
    name = chunks[0] if chunks else raw

    # "Tagline | Brand": prefer the chunk whose compact form matches the domain.
    brand = _compact(_domain_brand(site_url)) if site_url else ""
    if brand and len(chunks) > 1:
        for chunk in chunks:
            c = _compact(chunk)
            if c and (c == brand or (len(min(c, brand, key=len)) >= 4
                                     and (c in brand or brand in c))):
                name = chunk
                break

    # Cut a trailing tagline sentence ("Acme Corp provides …" -> "Acme Corp").
    m = _NAME_TAGLINE_RE.search(name)
    if m and m.start() > 0:
        name = name[:m.start()].strip()
    # Long, comma-separated keyword stuffing -> keep the first clause, capped.
    if len(name.split()) > _NAME_MAX_WORDS:
        name = name.split(",")[0].strip()
    if len(name.split()) > _NAME_MAX_WORDS:
        name = " ".join(name.split()[:_NAME_MAX_WORDS])
    return name or raw


def extract_favicon(soup, base_url):
    """Best favicon URL for use as the company logo.

    Prefers declared <link rel="...icon"> tags (apple-touch-icon and larger
    `sizes` win), and falls back to the conventional /favicon.ico. Relative hrefs
    are resolved against the homepage URL. The user's rule of thumb: the logo is
    mostly just the favicon, so this is the primary logo source.
    """
    best_score, best_url = -1, ""
    for tag in soup.find_all("link", href=True):
        rel = tag.get("rel") or []
        rel = " ".join(rel).lower() if isinstance(rel, list) else str(rel).lower()
        if "icon" not in rel:
            continue
        score = 0
        if "apple-touch" in rel:
            score += 1000  # apple-touch-icons are large, square PNGs — ideal
        m = re.search(r"(\d+)x\d+", tag.get("sizes", "") or "")
        if m:
            score += int(m.group(1))
        if score > best_score:
            best_score = score
            best_url = urljoin(base_url, tag["href"].strip())
    if best_url:
        return best_url
    parsed = urlparse(base_url)
    if parsed.scheme and parsed.netloc:
        return f"{parsed.scheme}://{parsed.netloc}/favicon.ico"
    return ""


# schema.org @types that denote a company/organization.
_ORG_TYPES = {"organization", "corporation", "localbusiness", "ngo",
              "educationalorganization", "softwareapplication"}

# A page is a real "About/Company" page only if its LAST path segment starts with
# one of these — so /about and /about-acme qualify, but /about-acme/webinars or
# /about/privacy-policy (deep noise pages) do not.
_ABOUT_SEGMENT_RE = re.compile(
    r"^(about|about-us|aboutus|company|who-we-are|our-story|overview|mission)([-_]|$)",
    re.I)
# Words that mark a sub-page as NOT a company description, even under /about/.
_NON_ABOUT_WORDS = ("privacy", "career", "job", "partner", "webinar", "policy",
                    "policies", "accessibility", "conduct", "terms", "cookie",
                    "legal", "press", "news", "blog", "event", "investor",
                    "support", "contact", "sitemap", "login", "award")
# A homepage description that reads like a storefront pitch is a poor company
# description (e.g. Meta's shop). Penalised so an About page can win instead.
_COMMERCE_RE = re.compile(r"^\s*(shop|buy|order|browse)\b|add to cart|shop now|buy now",
                          re.I)


def _last_path_segment(url):
    path = urlparse(url).path.rstrip("/")
    return path.rsplit("/", 1)[-1].lower() if path else ""


def _is_about_page(url):
    seg = _last_path_segment(url)
    if not seg or any(w in seg for w in _NON_ABOUT_WORDS):
        return False
    return bool(_ABOUT_SEGMENT_RE.match(seg))


def extract_company_info(homepage, soup):
    """Extract company identity with full provenance.

    Returns a dict whose `company_name`/`description`/`logo` are `Field` objects
    (value + source + method) and which also carries `address`, `social_links`.
    JSON-LD is preferred; meta tags and <title> are explicit fallbacks.
    """
    url = homepage.url
    info = {
        "company_name": Field(),
        "description": Field(),
        "logo": Field(),
        "social_links": [],
    }

    for block in parse_json_ld(soup):
        if not _ld_type_matches(block, _ORG_TYPES):
            continue
        if not info["company_name"].value and block.get("name"):
            info["company_name"] = Field(block["name"].strip(), url, Method.JSON_LD)
        if not info["description"].value and block.get("description"):
            info["description"] = Field(block["description"].strip(), url, Method.JSON_LD)
        same_as = block.get("sameAs")
        if isinstance(same_as, list):
            info["social_links"].extend([s for s in same_as if isinstance(s, str)])
        elif isinstance(same_as, str):
            info["social_links"].append(same_as)
        break  # first matching org block wins

    # Company name — JSON-LD wins; otherwise clean up og:site_name / og:title /
    # <title> so we keep just the name, not the marketing tagline.
    if not info["company_name"].value:
        content, _name = _meta_with_method(soup, "og:site_name", "og:title")
        if content:
            info["company_name"] = Field(
                _clean_company_name(content, url), url, Method.META_TAG)
        elif homepage.title:
            info["company_name"] = Field(
                _clean_company_name(homepage.title, url), url, Method.TITLE_TAG)

    if not info["description"].value:
        content, _name = _meta_with_method(soup, "og:description", "description")
        if content:
            info["description"] = Field(content, url, Method.META_TAG)

    # Logo — the favicon is the simple, reliable choice and is almost always
    # present (declared <link icon> or the conventional /favicon.ico).
    favicon = extract_favicon(soup, url)
    if favicon:
        info["logo"] = Field(favicon, url, Method.FAVICON)

    return info


def select_description(pages, soups_by_url):
    """Pick the best *company* description across crawled pages.

    Scored so the right source wins for both a normal site and a storefront:
        JSON-LD Organization description (any page) : 5  (authoritative)
        homepage meta, not a storefront pitch       : 4  (the usual elevator pitch)
        real About/Company page meta                : 3
        homepage meta that reads like a store        : 2  (fallback)
    Only the homepage and strict About pages are considered for meta text, so deep
    noise pages (webinars, privacy, careers) are ignored entirely. Ties break toward
    the longer (more substantive) text. Returns a Field or empty.
    """
    home_url = pages[0].url if pages else ""
    best_key = None
    best_field = None

    def consider(field, score):
        nonlocal best_key, best_field
        key = (score, min(len(field.value), 300))
        if best_key is None or key > best_key:
            best_key, best_field = key, field

    for page in pages:
        soup = soups_by_url.get(page.url)
        if soup is None:
            continue

        # JSON-LD organization description is authoritative — accept from any page.
        for block in parse_json_ld(soup):
            if _ld_type_matches(block, _ORG_TYPES) and block.get("description"):
                consider(Field(block["description"].strip(), page.url, Method.JSON_LD), 5)
                break

        # Meta text only from the homepage or a strict About page (skip noise pages).
        is_home = page.url == home_url
        is_about = _is_about_page(page.url)
        if not (is_home or is_about):
            continue
        content, _name = _meta_with_method(soup, "og:description", "description")
        if not content:
            continue
        content = content.strip()
        if is_home:
            score = 2 if _COMMERCE_RE.search(content) else 4
        else:
            score = 3
        consider(Field(content, page.url, Method.META_TAG), score)

    return best_field or Field()


# --------------------------------------------------------------------------- #
# Contacts: emails, phones, addresses
# --------------------------------------------------------------------------- #
def _clean_email(email):
    email = email.strip().strip(".").lower()
    if len(email) > 100:
        return None
    if any(b in email for b in EMAIL_BLOCKLIST_SUBSTR):
        return None
    return email


def extract_emails(pages):
    """pages: list[CrawledPage] -> list[Email] (deduped, lowest-source kept)."""
    found = {}
    for page in pages:
        if not page.html:
            continue
        for match in EMAIL_RE.findall(page.html):
            cleaned = _clean_email(match)
            if cleaned and cleaned not in found:
                found[cleaned] = Email(value=cleaned, source=page.url)
    return list(found.values())


def _valid_phone(raw):
    digits = re.sub(r"\D", "", raw)
    # Reject things that are clearly not phone numbers (dates, ids, prices).
    return 7 <= len(digits) <= 15


def extract_phones(pages):
    """Extract phone numbers, preferring tel: links, then visible text."""
    found = {}
    for page in pages:
        if not page.html:
            continue
        # tel: links are the most reliable source.
        for m in re.findall(r'tel:([+0-9()\s.\-]{7,})', page.html):
            raw = m.strip()
            digits = re.sub(r"\D", "", raw)
            if _valid_phone(raw) and digits not in found:
                found[digits] = Phone(
                    value="+" + digits if raw.strip().startswith("+") else digits,
                    raw=raw, source=page.url, method=Method.TEL_LINK)
        # Visible-text fallback. Use finditer + group(0): the subscriber digits
        # live outside any capture group, so findall/join would truncate them.
        for match in PHONE_RE.finditer(page.text or ""):
            raw = match.group(0).strip()
            if not raw:
                continue
            digits = re.sub(r"\D", "", raw)
            if _valid_phone(raw) and digits not in found:
                value = ("+" + digits) if raw.startswith("+") else digits
                found[digits] = Phone(value=value, raw=raw, source=page.url,
                                      method=Method.REGEX)
    return list(found.values())


def extract_addresses(pages, soups_by_url, company_info):
    """Pull likely business addresses from JSON-LD (high confidence) and
    contact-page PostalAddress / text heuristics (lower confidence)."""
    addresses = []
    seen = set()

    def add(value, source, conf, method):
        key = re.sub(r"\s+", " ", value).strip().lower()
        if value and key not in seen:
            seen.add(key)
            addresses.append(Address(value=value.strip(), source=source,
                                     confidence=conf, method=method))

    # 1. From company JSON-LD (already assembled).
    if company_info.get("address"):
        add(company_info["address"], company_info.get("address_source", ""),
            0.9, Method.JSON_LD)

    # 2. From any PostalAddress JSON-LD on any page.
    for page in pages:
        soup = soups_by_url.get(page.url)
        if soup is None:
            continue
        for block in parse_json_ld(soup):
            addr = block.get("address")
            if isinstance(addr, dict):
                parts = [addr.get(k, "") for k in
                         ("streetAddress", "addressLocality", "addressRegion",
                          "postalCode", "addressCountry")]
                value = ", ".join(p for p in parts if p)
                if value:
                    add(value, page.url, 0.85, Method.JSON_LD)

    # 3. Text heuristic on contact pages: lines with a postal-code-like token.
    postal_re = re.compile(r"\b\d{5,6}\b")
    for page in pages:
        if "contact" not in page.url.lower():
            continue
        for line in (page.text or "").split("  "):
            line = line.strip()
            if (30 <= len(line) <= 160 and postal_re.search(line)
                    and re.search(r"\d", line) and "," in line):
                add(line, page.url, 0.5, Method.TEXT_HEURISTIC)
                break
    return addresses


# --------------------------------------------------------------------------- #
# Social profiles
# --------------------------------------------------------------------------- #
def extract_social_profiles(pages, soups_by_url, extra_links=None):
    """Return dict network -> SocialProfile(value, source, method).

    JSON-LD `sameAs` links are considered first (method JSON-LD); anchor links
    discovered while crawling are the fallback (method Social Rule).
    """
    profiles = {k: SocialProfile() for k in
                ("linkedin", "twitter", "github", "facebook", "instagram", "youtube")}

    # candidates: list of (href, source_url, method) — JSON-LD first.
    home_url = pages[0].url if pages else ""
    candidates = [(link, home_url, Method.JSON_LD) for link in (extra_links or [])]
    for page in pages:
        soup = soups_by_url.get(page.url)
        if soup is None:
            continue
        for a in soup.find_all("a", href=True):
            candidates.append((a["href"].strip(), page.url, Method.SOCIAL_RULE))

    for href, source, method in candidates:
        if not href or SOCIAL_NEGATIVE.search(href):
            continue
        # Resolve protocol-relative ("//linkedin.com/x") and relative hrefs to an
        # absolute https URL, using the page's scheme — otherwise we store/render a
        # broken link that isn't even recognised as external.
        url = urljoin(source, href.strip())
        for network, pattern in SOCIAL_PATTERNS.items():
            if profiles[network].value:
                continue
            if pattern.search(url):
                profiles[network] = SocialProfile(value=url, source=source, method=method)
    return profiles


# --------------------------------------------------------------------------- #
# Technology detection
# --------------------------------------------------------------------------- #
def detect_technologies(pages, response_headers_by_url=None):
    """Signature match against HTML + response headers. Returns list[Technology]."""
    response_headers_by_url = response_headers_by_url or {}
    detected = {}
    for page in pages:
        if not page.html:
            continue
        haystack = page.html.lower()
        headers = " ".join(
            f"{k}:{v}" for k, v in response_headers_by_url.get(page.url, {}).items()
        ).lower()
        combined = haystack + " " + headers
        for tech, signatures in TECH_SIGNATURES.items():
            if tech in detected:
                continue
            for sig in signatures:
                if sig.lower() in combined:
                    detected[tech] = Technology(name=tech, source=page.url, evidence=sig)
                    break
    return list(detected.values())


# --------------------------------------------------------------------------- #
# Team member discovery
# --------------------------------------------------------------------------- #
_NAME_RE = re.compile(r"^[A-Z][a-z'’.-]+(?:\s+[A-Z][a-z'’.-]+){1,2}$")

# Words that frequently start a capitalized phrase but are not personal names.
# Used to reject section headings / nav labels like "About Frappe" or "Team Members".
NAME_STOPWORDS = {
    "about", "team", "our", "meet", "the", "join", "contact", "home", "log",
    "login", "welcome", "products", "partners", "events", "community", "careers",
    "leadership", "company", "people", "investors", "contents", "testimonials",
    "incubator", "members", "member", "founders", "management", "technologies",
    "technology", "inc", "ltd", "llc", "gmbh", "privacy", "terms", "blog",
    # Legal-entity suffixes — a "name" carrying these is a company, not a person.
    "limited", "corp", "corporation", "plc", "pvt", "holdings", "industries",
    "enterprises", "securities",
    "news", "support", "pricing", "features", "solutions", "services",
    # Designation/role words — a "name" made only of these is a title, not a person.
    "senior", "junior", "vice", "president", "chief", "officer", "director",
    "head", "manager", "lead", "founder", "cofounder", "ceo", "cto", "coo",
    "cfo", "cmo", "cpo", "executive", "engineer", "engineering", "developer",
    "strategic", "supervisor", "specialist", "associate", "analyst", "consultant",
    "coordinator", "administrator", "representative", "intern", "staff", "advisor",
    "principal", "partner", "owner", "founding", "global", "regional",
    # Call-to-action / UI / link text that looks capitalized but isn't a person.
    "read", "more", "learn", "click", "view", "see", "explore", "discover",
    "get", "start", "started", "sign", "signup", "subscribe", "download",
    "watch", "play", "shop", "buy", "order", "follow", "share", "menu", "close",
    "open", "next", "previous", "prev", "back", "search", "submit", "send",
    "apply", "register", "book", "schedule", "request", "demo", "free", "new",
    "all", "show", "hide", "continue", "skip", "try", "go", "find", "browse",
    "select", "choose", "upload", "copy", "print", "help", "faq", "settings",
    "account", "profile", "dashboard", "overview", "details", "summary",
    "latest", "featured", "popular", "trending", "recent", "view all",
}


def _looks_like_name(text):
    text = (text or "").strip()
    if not (4 <= len(text) <= 40) or not _NAME_RE.match(text):
        return False
    tokens = text.split()
    # Reject if any token is a stopword (covers "About Frappe", "Team Members",
    # "Frappe Technologies", "Frappe Inc", etc.).
    if any(tok.lower().strip(".") in NAME_STOPWORDS for tok in tokens):
        return False
    return True


def _designation_in(text):
    # Word-boundary match, longest titles first. A naive substring test wrongly
    # fired "CTO" inside "Dire-CTO-r", tagging every board director a CTO.
    low = (text or "").lower()
    for kw in DESIGNATION_KEYWORDS:
        k = kw.lower().strip()
        if re.search(r"(?<!\w)" + re.escape(k) + r"(?!\w)", low):
            return kw.strip()
    return ""


def _nearby_designation(node, name):
    """Find a designation associated with `name` *only* when it sits in a small,
    immediately-adjacent block — not anywhere on a busy page.

    Returns (designation, confidence) or ("", 0.0). We check, in order:
      1. the name node's immediate parent, if that parent's text is short;
      2. the parent's next/previous sibling element, if short.
    Short = the designation is genuinely next to the name, not a page-wide hit.
    """
    MAX_BLOCK = 90  # chars; a real "Name — Title" card is short

    parent = node.parent
    if parent is None:
        return "", 0.0

    block = parent.get_text(" ", strip=True)
    residue = block.replace(name, "").strip()
    if len(block) <= MAX_BLOCK:
        desig = _designation_in(residue)
        if desig:
            return desig, 0.85

    # Adjacent sibling elements (title often lives in the next <div>/<p>/<span>).
    for sib in (parent.find_next_sibling(), parent.find_previous_sibling()):
        if sib is None or not hasattr(sib, "get_text"):
            continue
        sib_text = sib.get_text(" ", strip=True)
        if 0 < len(sib_text) <= MAX_BLOCK:
            desig = _designation_in(sib_text)
            if desig:
                return desig, 0.7
    return "", 0.0


_NAME_SKIP_ANCESTORS = {"form", "select", "option", "datalist", "label",
                        "button", "nav", "footer", "header"}


def discover_team_members(pages, soups_by_url):
    """Find (name, designation) pairs on team/leadership/about pages.

    Only relevant pages are scanned. A node must look like a person name AND have
    a designation in an immediately-adjacent, short text block. This deliberately
    favours precision (few, correct entries) over recall.
    """
    contacts = {}
    relevant = [p for p in pages
                if any(k in p.url.lower()
                       for k in ("team", "leadership", "about", "people",
                                 "founders", "management", "company"))]
    for page in relevant:
        soup = soups_by_url.get(page.url)
        if soup is None:
            continue
        for node in soup.find_all(string=_looks_like_name):
            # Skip form controls (a country <select>, enquiry-type <option>, field
            # <label>) and page chrome — these aren't bio cards. This is what let
            # "Costa Rica", "Enquiry Type" and "Customer Complaints" through.
            if any(getattr(p, "name", None) in _NAME_SKIP_ANCESTORS
                   for p in node.parents):
                continue
            name = " ".join(node.split())  # normalise internal whitespace
            designation, confidence = _nearby_designation(node, name)
            if designation and confidence >= 0.6 and name not in contacts:
                contacts[name] = Contact(name=name, designation=designation,
                                         source=page.url, confidence=confidence)
    return list(contacts.values())


# --------------------------------------------------------------------------- #
# Business signals
# --------------------------------------------------------------------------- #
def detect_signals(pages):
    signals = Signals()
    snippets = []
    for page in pages:
        text = (page.text or "")
        low = text.lower()
        for signal_name, keywords in SIGNAL_KEYWORDS.items():
            for kw in keywords:
                idx = low.find(kw)
                if idx == -1:
                    continue
                setattr(signals, signal_name, True)
                start = max(0, idx - 40)
                end = min(len(text), idx + len(kw) + 40)
                snippet = text[start:end].strip()
                snippets.append({"signal": signal_name, "keyword": kw,
                                 "snippet": snippet, "source": page.url})
                break  # one snippet per keyword-group per page
    # Dedupe snippets by (signal, snippet text).
    uniq, seen = [], set()
    for s in snippets:
        key = (s["signal"], s["snippet"].lower())
        if key not in seen:
            seen.add(key)
            uniq.append(s)
    signals.matched_snippets = uniq[:20]
    return signals


# --------------------------------------------------------------------------- #
# Employee count (heuristic, from the company's own pages)
# --------------------------------------------------------------------------- #
# Maps an explicit headcount to the CRM `no_of_employees` select buckets.
EMPLOYEE_BUCKETS = [
    (10, "1-10"),
    (50, "11-50"),
    (200, "51-200"),
    (500, "201-500"),
    (1000, "501-1000"),
    (float("inf"), "1000+"),
]

# Headcount phrases, split by signal strength so an unambiguous company-size
# keyword always beats an ambiguous one. STRONG keywords ("employees", "staff",
# "team members", "workforce") name the whole company; WEAK ones ("team of N",
# "N people") are often a sub-team or marketing copy. Deliberately conservative —
# generic text like "1000 customers" matches nothing.
_NUM = r"(\d[\d,]*)"
_QUAL = r"(?:over\s+|more than\s+|around\s+|nearly\s+|approximately\s+)?"
EMPLOYEE_PATTERNS_STRONG = [
    re.compile(r"\b" + _QUAL + _NUM +
               r"\s*\+?\s*(?:employees|staff members|staff|team members|"
               r"workforce|full[- ]time employees|ftes?)\b", re.I),
    re.compile(r"\b(?:workforce|headcount)\s+of\s+" + _QUAL + _NUM + r"\b", re.I),
]
EMPLOYEE_PATTERNS_WEAK = [
    re.compile(r"\bteam of\s+" + _QUAL + _NUM + r"\b", re.I),
    re.compile(r"\b" + _QUAL + _NUM + r"\s*\+?\s*people\b", re.I),
]


def _employee_bucket(n):
    for ceiling, label in EMPLOYEE_BUCKETS:
        if n <= ceiling:
            return label
    return "1000+"


def _headcount_matches(pages, patterns):
    """(count, source) for every plausible headcount produced by `patterns`."""
    out = []
    for page in pages:
        text = page.text or ""
        for pattern in patterns:
            for m in pattern.finditer(text):
                raw = m.group(1).replace(",", "")
                if not raw.isdigit():
                    continue
                n = int(raw)
                if 2 <= n <= 2_000_000:  # ignore noise (ids, single founder)
                    out.append((n, page.url))
    return out


def estimate_employees(pages):
    """Best-effort headcount from explicit phrases on the company's own pages.
    Returns a Field(bucket, source, method) or empty.

    Strong company-size keywords win over ambiguous ones; within the chosen tier
    we take the largest plausible number (a sub-team mention shouldn't shrink a
    stated company size). Heuristic by design — no external API.
    """
    matches = (_headcount_matches(pages, EMPLOYEE_PATTERNS_STRONG)
               or _headcount_matches(pages, EMPLOYEE_PATTERNS_WEAK))
    if not matches:
        return Field()
    count, source = max(matches, key=lambda cs: cs[0])
    return Field(_employee_bucket(count), source, Method.EMPLOYEE_HEURISTIC)


# --------------------------------------------------------------------------- #
# Industry classification
# --------------------------------------------------------------------------- #
def _kw_count(keyword, text):
    """Word-boundary count of `keyword` in `text` (so "brand" != "branding")."""
    return len(re.findall(r"(?<!\w)" + re.escape(keyword) + r"(?!\w)", text))


def classify_industry(pages, company_info):
    """Rule-based industry from the HOMEPAGE's headline text only — company name,
    description, the homepage <title> and its headings. Body/footer text and
    subpages are deliberately excluded: footer copy made the old version label
    everything "Marketing", and subpage headings (careers, sustainability, …) leak
    unrelated topics (e.g. a sustainability page tagging a conglomerate "Energy").
    Returns (industry, confidence 0-1), or ("", 0.0) when the signal is too weak.
    """
    def _val(key):
        f = company_info.get(key)
        return getattr(f, "value", f) or ""

    # Homepage headline corpus only — no body, no URLs, no subpages.
    weighted_text = [(_val("company_name"), 3), (_val("description"), 3)]
    if pages:
        home = pages[0]
        weighted_text.append((home.title, 3))
        weighted_text.append((" ".join(home.headings), 2))

    scores = {industry: 0 for industry in INDUSTRY_KEYWORDS}
    for industry, keywords in INDUSTRY_KEYWORDS.items():
        for text, weight in weighted_text:
            low = (text or "").lower()
            for kw in keywords:
                scores[industry] += _kw_count(kw, low) * weight

    total = sum(scores.values())
    best = max(scores, key=scores.get) if total else ""
    if not total or scores[best] < INDUSTRY_MIN_SCORE:
        return "", 0.0
    confidence = scores[best] / total
    if confidence < INDUSTRY_MIN_CONFIDENCE:
        return "", 0.0   # ambiguous — better blank than a wrong guess
    return best, round(confidence, 2)
