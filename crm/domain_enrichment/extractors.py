# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Generic, config-driven extractors.

No literal keyword/industry/social tables here: classifiers iterate over
``cfg.rules_by_type[...]``, honoring each rule's ``match_scope``, ``weight`` and
compiled patterns. JSON-LD parsing, the favicon scorer, readability diagnosis,
email/phone regex, and company-name cleaning stay as plain mechanics -- not
tunable knowledge, so not pushed into doctypes.
"""

from __future__ import annotations

import json
import re
from urllib.parse import urljoin, urlparse

from .config import INDUSTRY_MIN_CONFIDENCE, INDUSTRY_MIN_SCORE
from .result import (
	Email,
	Field,
	Method,
	Phone,
	SocialProfile,
)

# --------------------------------------------------------------------------- #
# Regexes (mechanics)
# --------------------------------------------------------------------------- #
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")

PHONE_RE = re.compile(
	r"""(?<!\w)
    (\+?\d{1,3}[\s.-]?)?      # optional country code
    (\(?\d{2,4}\)?[\s.-]?)    # area / first group
    \d{3,4}[\s.-]?\d{3,4}     # subscriber number
    (?!\w)""",
	re.VERBOSE,
)

# Emails that are almost always noise (asset hashes, example domains, images).
EMAIL_BLOCKLIST_SUBSTR = (
	"example.com",
	"sentry.io",
	"@2x",
	"@3x",
	".png",
	".jpg",
	".gif",
	".svg",
	".webp",
	"your-email",
	"email@",
)

# Generic landing pages we should not treat as a social profile.
SOCIAL_NEGATIVE = re.compile(r"/(sharer|share|intent|home|login|signup|privacy|tos)\b", re.I)


# --------------------------------------------------------------------------- #
# Generic rule executors
# --------------------------------------------------------------------------- #
SCOPE_HEADLINE = "Headline"
SCOPE_FULL_TEXT = "Full Text"
SCOPE_HTML = "HTML"
SCOPE_HEADERS = "Headers"
SCOPE_URL = "URL"


def apply_keyword_rules(text_by_scope: dict, rules: list) -> dict:
	"""Returns ``{label: weighted_score}`` -- ``label`` is the rule's industry
	(Industry rules) or target_value (everything else)."""
	scores: dict = {}
	for rule in rules:
		text = text_by_scope.get(rule.match_scope, "")
		hits = rule.matches(text)
		if hits:
			scores[rule.label] = scores.get(rule.label, 0.0) + hits * (rule.weight or 1.0)
	return scores


# --------------------------------------------------------------------------- #
# JSON-LD (mechanics)
# --------------------------------------------------------------------------- #
def parse_json_ld(soup):
	blocks = []
	for tag in soup.find_all("script", attrs={"type": "application/ld+json"}):
		raw = tag.string or tag.get_text() or ""
		if not raw.strip():
			continue
		try:
			data = json.loads(raw)
		except (ValueError, TypeError):
			continue
		if isinstance(data, dict):
			if "@graph" in data and isinstance(data["@graph"], list):
				blocks.extend([d for d in data["@graph"] if isinstance(d, dict)])
			else:
				blocks.append(data)
		elif isinstance(data, list):
			blocks.extend([d for d in data if isinstance(d, dict)])
	return blocks


def _ld_type_matches(block, wanted):
	t = block.get("@type", "")
	types = t if isinstance(t, list) else [t]
	return any(str(x).lower() in wanted for x in types)


# --------------------------------------------------------------------------- #
# Readability diagnosis (mechanics)
# --------------------------------------------------------------------------- #
WAF_MARKERS_STRONG = (
	"_incapsula_resource",
	"incapsula",
	"cf-browser-verification",
	"just a moment",
	"attention required",
	"ddos protection",
	"are you a human",
)
WAF_MARKERS_WEAK = (
	"captcha",
	"please enable javascript",
	"enable cookies to continue",
	"access denied",
)
WAF_WEAK_TEXT_THRESHOLD = 1000

READABILITY_MESSAGES = {
	"unreachable": "Couldn't reach this website (it timed out or refused the connection).",
	"blocked": (
		"This website is behind bot protection, so its content can't be read. "
		"Try the company's corporate domain (e.g. acme.com vs shop.acme.com)."
	),
	"empty": (
		"This site's main content is JavaScript-rendered; only page metadata "
		"(title/description/logo) could be read, so some fields may be blank."
	),
}


def diagnose_readability(pages):
	"""Judge the homepage: '' (readable), 'blocked', 'empty', or 'unreachable'."""
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
	text_len = len(home.text or "")
	if any(marker in blob for marker in WAF_MARKERS_STRONG):
		return "blocked"
	if text_len < WAF_WEAK_TEXT_THRESHOLD and any(marker in blob for marker in WAF_MARKERS_WEAK):
		return "blocked"
	if text_len < 200:
		return "empty"
	return ""


# --------------------------------------------------------------------------- #
# Company information (mechanics)
# --------------------------------------------------------------------------- #
def _meta_with_method(soup, *names):
	for name in names:
		tag = soup.find("meta", attrs={"property": name}) or soup.find("meta", attrs={"name": name})
		if tag and tag.get("content"):
			return tag["content"].strip(), name
	return "", ""


# A company name is usually the first chunk of a page <title>, before a separator.
_NAME_SPLIT_RE = re.compile(r"\s*\|\s*|\s+[-–—•·]\s+|\s*:\s")
_NAME_TAGLINE_RE = re.compile(
	r"\s+(?:has|have|is|are|was|were|offers?|provides?|delivers?|helps?|"
	r"enables?|builds?|makes?|creates?|specializes?|brings?|"
	r"empowers?|powers?|leads?|connects?)\b",
	re.I,
)
_NAME_MAX_WORDS = 6


def _domain_brand(url):
	netloc = (urlparse(url or "").netloc or "").lower().split(":")[0]
	if netloc.startswith("www."):
		netloc = netloc[4:]
	labels = [label for label in netloc.split(".") if label]
	return labels[-2] if len(labels) >= 2 else (labels[0] if labels else "")


def _compact(text):
	return re.sub(r"[^a-z0-9]", "", (text or "").lower())


def _clean_company_name(raw, site_url=""):
	"""Trim a page title / og:title down to just the company name."""
	raw = (raw or "").strip()
	if not raw:
		return ""
	chunks = [c.strip() for c in _NAME_SPLIT_RE.split(raw) if c.strip()]
	name = chunks[0] if chunks else raw

	brand = _compact(_domain_brand(site_url)) if site_url else ""
	if brand and len(chunks) > 1:
		for chunk in chunks:
			c = _compact(chunk)
			if c and (c == brand or (len(min(c, brand, key=len)) >= 4 and (c in brand or brand in c))):
				name = chunk
				break

	m = _NAME_TAGLINE_RE.search(name)
	if m and m.start() > 0:
		name = name[: m.start()].strip()
	if len(name.split()) > _NAME_MAX_WORDS:
		name = name.split(",")[0].strip()
	if len(name.split()) > _NAME_MAX_WORDS:
		name = " ".join(name.split()[:_NAME_MAX_WORDS])
	return name or raw


# apple-touch-icons are 180px by convention when no explicit size is declared.
_APPLE_TOUCH_PX = 180


def _safe_url(base_url, raw):
	"""Resolve ``raw`` against ``base_url``; return it only if it's a non-empty
	``http(s)`` URL. Rejects ``javascript:``/``data:`` schemes a crawled site could
	inject into a stored logo/image/icon field (stored-XSS defense)."""
	raw = (raw or "").strip()
	if not raw:
		return ""
	# urljoin() leaves javascript:/data: schemes as-is, so check the raw scheme
	# first, then re-check the resolved URL for relative inputs.
	scheme = urlparse(raw).scheme.lower()
	if scheme and scheme not in ("http", "https"):
		return ""
	resolved = urljoin(base_url, raw)
	return resolved if urlparse(resolved).scheme in ("http", "https") else ""


def _best_icon(soup, base_url):
	"""Best ``<link rel=icon>`` candidate: scalable SVG beats any raster, then
	largest declared size wins."""
	candidates = []
	for tag in soup.find_all("link", href=True):
		rel = tag.get("rel") or []
		rel = " ".join(rel).lower() if isinstance(rel, list) else str(rel).lower()
		if "icon" not in rel:
			continue
		href = tag["href"].strip()
		safe = _safe_url(base_url, href)
		if not safe:
			continue
		is_svg = (
			"svg" in (tag.get("type") or "").lower()
			or href.lower().split("?")[0].endswith(".svg")
			or "mask-icon" in rel
		)
		m = re.search(r"(\d+)x\d+", tag.get("sizes", "") or "")
		px = int(m.group(1)) if m else (_APPLE_TOUCH_PX if "apple-touch" in rel else 0)
		candidates.append(((1 if is_svg else 0, px), safe))
	if not candidates:
		return ""
	candidates.sort(key=lambda c: c[0], reverse=True)
	return candidates[0][1]


def extract_logo(soup, base_url):
	"""The company's link icon -- a crisp, square brand mark, not the wider
	social-share image (``og:image`` is usually a banner; see :func:`extract_image`).
	Priority: SVG > largest declared raster/apple-touch > ``/favicon.ico`` fallback.
	"""
	icon_url = _best_icon(soup, base_url)
	if icon_url:
		return Field(icon_url, base_url, Method.FAVICON)

	parsed = urlparse(base_url)
	if parsed.scheme and parsed.netloc:
		return Field(f"{parsed.scheme}://{parsed.netloc}/favicon.ico", base_url, Method.FAVICON)
	return Field()


def extract_image(soup, base_url):
	"""The larger brand/social image (JSON-LD ``Organization.logo`` -> ``og:image``/
	``twitter:image``), NOT the company logo -- see :func:`extract_logo`. Returns a
	:class:`Field`, empty if none declared."""
	for block in parse_json_ld(soup):
		if not _ld_type_matches(block, _ORG_TYPES):
			continue
		logo = block.get("logo")
		url = logo.get("url") if isinstance(logo, dict) else (logo if isinstance(logo, str) else "")
		safe = _safe_url(base_url, url)
		if safe:
			return Field(safe, base_url, Method.JSON_LD)

	og_content, _name = _meta_with_method(soup, "og:image", "og:image:url", "twitter:image")
	safe = _safe_url(base_url, og_content)
	if safe:
		return Field(safe, base_url, Method.META_TAG)
	return Field()


# schema.org @types that denote a company/organization.
_ORG_TYPES = {
	"organization",
	"corporation",
	"localbusiness",
	"ngo",
	"educationalorganization",
	"softwareapplication",
}

# Full-segment match, not a prefix: "about-our-reporting" (an ESG page) must not
# qualify just because it starts with "about-".
_ABOUT_SEGMENT_RE = re.compile(
	r"^(about|about-us|aboutus|company|who-we-are|our-story|overview|mission)$",
	re.I,
)
_NON_ABOUT_WORDS = (
	"privacy",
	"career",
	"job",
	"partner",
	"webinar",
	"policy",
	"policies",
	"accessibility",
	"conduct",
	"terms",
	"cookie",
	"legal",
	"press",
	"news",
	"blog",
	"event",
	"investor",
	"support",
	"contact",
	"sitemap",
	"login",
	"award",
)
_COMMERCE_RE = re.compile(r"^\s*(shop|buy|order|browse)\b|add to cart|shop now|buy now", re.I)


def _last_path_segment(url):
	path = urlparse(url).path.rstrip("/")
	return path.rsplit("/", 1)[-1].lower() if path else ""


def _is_about_page(url):
	seg = _last_path_segment(url)
	if not seg or any(w in seg for w in _NON_ABOUT_WORDS):
		return False
	return bool(_ABOUT_SEGMENT_RE.match(seg))


def extract_company_info(homepage, soup):
	url = homepage.url
	info = {
		"company_name": Field(),
		"description": Field(),
		"logo": Field(),
		"image": Field(),
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

	if not info["company_name"].value:
		content, _name = _meta_with_method(soup, "og:site_name", "og:title")
		if content:
			info["company_name"] = Field(_clean_company_name(content, url), url, Method.META_TAG)
		elif homepage.title:
			info["company_name"] = Field(_clean_company_name(homepage.title, url), url, Method.TITLE_TAG)

	if not info["description"].value:
		content, _name = _meta_with_method(soup, "og:description", "description")
		if content:
			info["description"] = Field(content, url, Method.META_TAG)

	info["logo"] = extract_logo(soup, url)
	info["image"] = extract_image(soup, url)

	return info


_NON_CONTENT_PARENTS = {"nav", "header", "footer", "aside", "form"}
_MIN_PARAGRAPH_LEN = 80
_MAX_PARAGRAPHS_SCANNED = 6


def _company_name_hits(text, company_name):
	name = (company_name or "").strip()
	if not name:
		return 0
	return len(re.findall(rf"\b{re.escape(name)}\b", text, re.IGNORECASE))


def first_paragraph(soup, industry_rules=None, company_name=""):
	"""Best substantial body paragraph on a page. Scores up to
	``_MAX_PARAGRAPHS_SCANNED`` qualifying ``<p>`` tags by Industry-rule keyword hits
	(the same corpus ``classify_industry`` uses); ``company_name`` mentions only
	break ties, never outrank keyword signal. Read-only -- does not mutate ``soup``.
	"""
	candidates = []
	for p in soup.find_all("p"):
		if any(parent.name in _NON_CONTENT_PARENTS for parent in p.parents):
			continue
		text = " ".join((p.get_text(" ") or "").split())
		if len(text) < _MIN_PARAGRAPH_LEN or " " not in text:
			continue
		candidates.append(text)
		if len(candidates) >= _MAX_PARAGRAPHS_SCANNED:
			break

	if not candidates:
		return ""
	if not industry_rules:
		return candidates[0]

	# max() keeps the first-encountered element on ties, so document order still
	# wins when nothing scores higher (covers the "all zero hits" case for free).
	# Company-name hits are a separate tuple slot -- they can only break ties,
	# never add to the industry-hit count.
	return max(
		candidates,
		key=lambda text: (
			sum(rule.matches(text) for rule in industry_rules),
			_company_name_hits(text, company_name),
		),
	)


def select_description(pages, soups_by_url, industry_rules=None, company_name=""):
	"""Pick the best *company* description across crawled pages.

	Priority: JSON-LD ``Organization.description`` -> About-page body paragraph ->
	head ``og:description``/``<meta description>`` -> home-page body paragraph
	(last resort). ``industry_rules``/``company_name`` steer the body-paragraph
	fallbacks (see ``first_paragraph``).
	"""
	home_url = pages[0].url if pages else ""
	best_key = None
	best_field = None

	def consider(field_obj, score):
		nonlocal best_key, best_field
		if not field_obj.value:
			return
		key = (score, min(len(field_obj.value), 300))
		if best_key is None or key > best_key:
			best_key, best_field = key, field_obj

	for page in pages:
		soup = soups_by_url.get(page.url)
		if soup is None:
			continue

		is_home = page.url == home_url
		is_about = _is_about_page(page.url)

		for block in parse_json_ld(soup):
			if _ld_type_matches(block, _ORG_TYPES) and block.get("description"):
				consider(Field(block["description"].strip(), page.url, Method.JSON_LD), 6)
				break

		if is_about:
			consider(
				Field(first_paragraph(soup, industry_rules, company_name), page.url, Method.BODY_TEXT), 5
			)

		if is_home or is_about:
			content, _name = _meta_with_method(soup, "og:description", "description")
			if content:
				content = content.strip()
				score = 2 if (is_home and _COMMERCE_RE.search(content)) else 4
				consider(Field(content, page.url, Method.META_TAG), score)

		if is_home:
			consider(
				Field(first_paragraph(soup, industry_rules, company_name), page.url, Method.BODY_TEXT), 1
			)

	return best_field or Field()


# --------------------------------------------------------------------------- #
# Contacts: emails, phones (mechanics)
# --------------------------------------------------------------------------- #
def _clean_email(email):
	email = email.strip().strip(".").lower()
	if any(b in email for b in EMAIL_BLOCKLIST_SUBSTR):
		return None
	return email


def extract_emails(pages):
	found = {}
	for page in pages:
		if not page.html:
			continue
		for match in EMAIL_RE.findall(page.html):
			cleaned = _clean_email(match)
			if cleaned and cleaned not in found:
				found[cleaned] = Email(value=cleaned, source=page.url)
	return list(found.values())


# TODO: Need to make this robust by adding proper mechanics or using a
# thirdparty library like google/libphonenumbers
def _valid_phone(raw):
	# Requires an explicit "+" country-code prefix: a bare digit string is either
	# ambiguous local formatting or noise (stats, reference numbers) that happens
	# to look phone-shaped -- precision over recall.
	if not raw.strip().startswith("+"):
		return False
	digits = re.sub(r"\D", "", raw)
	return 7 <= len(digits) <= 15


def extract_phones(pages):
	found = {}
	for page in pages:
		if not page.html:
			continue
		for m in re.findall(r"tel:([+0-9()\s.\-]{7,})", page.html):
			raw = m.strip()
			digits = re.sub(r"\D", "", raw)
			if _valid_phone(raw) and digits not in found:
				found[digits] = Phone(
					value="+" + digits if raw.strip().startswith("+") else digits,
					raw=raw,
					source=page.url,
					method=Method.TEL_LINK,
				)
		for match in PHONE_RE.finditer(page.text or ""):
			raw = match.group(0).strip()
			if not raw:
				continue
			digits = re.sub(r"\D", "", raw)
			if _valid_phone(raw) and digits not in found:
				value = ("+" + digits) if raw.startswith("+") else digits
				found[digits] = Phone(value=value, raw=raw, source=page.url, method=Method.REGEX)
	return list(found.values())


# --------------------------------------------------------------------------- #
# Social profiles (config-driven via Social rules)
# --------------------------------------------------------------------------- #
def extract_social_profiles(pages, soups_by_url, social_rules, extra_links=None):
	"""Return dict network -> SocialProfile(value, source, method); each Social
	rule's ``target_value`` is the network name."""
	profiles = {rule.target_value: SocialProfile() for rule in social_rules}

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
		url = urljoin(source, href.strip())
		for rule in social_rules:
			network = rule.target_value
			if profiles[network].value:
				continue
			if any(rx.search(url) for rx, _raw in rule.patterns):
				profiles[network] = SocialProfile(value=url, source=source, method=method)
	return profiles


# --------------------------------------------------------------------------- #
# Industry classification (config-driven via Industry rules)
# --------------------------------------------------------------------------- #
def classify_industry(pages, company_info, industry_rules):
	"""Rule-based industry from the homepage's (and, when crawled, the About page's)
	headline corpus. Industry rules are typically seeded with ``match_scope='Headline'``
	(company name/description/title/headings, never body/footer). The homepage alone
	is often thin (stylized brand copy, no meta description), so a crawled About
	page's title/headings are folded in too. Returns (industry, confidence 0-1), or
	("", 0.0) when the signal is too weak.
	"""
	if not industry_rules:
		return "", 0.0

	def _val(key):
		f = company_info.get(key)
		return getattr(f, "value", f) or ""

	headline_parts = [_val("company_name"), _val("description")]
	if pages:
		home = pages[0]
		headline_parts.append(home.title or "")
		headline_parts.append(" ".join(home.headings))
		about = next((p for p in pages[1:] if _is_about_page(p.url)), None)
		if about:
			headline_parts.append(about.title or "")
			headline_parts.append(" ".join(about.headings))
	headline = " ".join(p for p in headline_parts if p).lower()

	# Same corpus under multiple scope keys so admins can re-scope rules without
	# code changes; default seed uses Headline.
	full_text = " ".join((p.text or "") for p in pages).lower()
	text_by_scope = {
		SCOPE_HEADLINE: headline,
		SCOPE_FULL_TEXT: full_text,
		SCOPE_HTML: full_text,
	}

	scores = apply_keyword_rules(text_by_scope, industry_rules)
	total = sum(scores.values())
	if not total:
		return "", 0.0
	best = max(scores, key=scores.get)
	if scores[best] < INDUSTRY_MIN_SCORE:
		return "", 0.0
	confidence = scores[best] / total
	if confidence < INDUSTRY_MIN_CONFIDENCE:
		return "", 0.0
	return best, round(confidence, 2)
