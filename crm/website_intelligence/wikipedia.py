"""Wikipedia description lookup — a clean, third-person company summary.

The website's own meta description is marketing copy ("Live news, investigations,
opinion, photos and video…"). Wikipedia's intro is a neutral third-person narrative
("The New York Times is an American daily newspaper…"), which reads far better in a
CRM. We prefer it, but ONLY when we can confirm we matched the right company:
Wikidata's "official website" (property P856) for the matched page must resolve to
the same registrable domain as the record's website. That domain check is what keeps
us from pasting the wrong "Apple"/"Phoenix"/"Orange" into a record.

Free, public, read-only — no API key, no paid enrichment provider. Never raises: any
failure (offline, no match, rate-limit) returns ("", "") so the caller falls back to
the website description.
"""

from __future__ import annotations

import re
from urllib.parse import urlparse

from .http_client import build_session

# Pronunciation glosses Wikipedia puts after a name, e.g. NVIDIA "( en-VID-ee-ə)".
# IPA respellings always carry non-ASCII letters, so drop parentheticals that do —
# this leaves useful ones like "(NYT)" or "(formerly X)" intact.
_PRONUNCIATION_RE = re.compile(r"\s*\([^)]*[^\x00-\x7f][^)]*\)")

WIKI_API = "https://en.wikipedia.org/w/api.php"
WIKIDATA_API = "https://www.wikidata.org/w/api.php"
TIMEOUT = 6
MAX_CHARS = 400  # keep it "simple" — roughly the first 1–3 sentences


def _registrable_domain(url: str) -> str:
    netloc = (urlparse(url or "").netloc or urlparse("//" + (url or "")).netloc or "")
    netloc = netloc.lower().split(":")[0]
    if netloc.startswith("www."):
        netloc = netloc[4:]
    return ".".join(netloc.split(".")[-2:]) if netloc.count(".") >= 1 else netloc


def _trim(text: str) -> str:
    """Strip pronunciation glosses, collapse whitespace, cut to ~the first
    couple of sentences."""
    text = _PRONUNCIATION_RE.sub("", text or "")
    text = " ".join(text.split())
    if len(text) <= MAX_CHARS:
        return text
    cut = text[:MAX_CHARS]
    end = max(cut.rfind(". "), cut.rfind("? "), cut.rfind("! "))
    return (cut[: end + 1] if end > 80 else cut.rstrip()) or text[:MAX_CHARS]


def _wikidata_domain_matches(session, qid: str, domain: str) -> bool:
    """True if the Wikidata entity's official website (P856) is on `domain`."""
    resp = session.get(
        WIKIDATA_API,
        params={"action": "wbgetclaims", "format": "json",
                "entity": qid, "property": "P856"},
        timeout=TIMEOUT,
    )
    claims = (resp.json().get("claims") or {}).get("P856") or []
    for claim in claims:
        url = (claim.get("mainsnak", {}).get("datavalue", {})
               .get("value", "") or "")
        if url and _registrable_domain(url) == domain:
            return True
    return False


def fetch_company_description(company_name: str, website: str, session=None):
    """Return (description, source_url) from Wikipedia for the company, or ("", "").

    The match is accepted only when the page's Wikidata "official website" shares the
    record's registrable domain — so we never attach a same-named but unrelated page.
    """
    company_name = (company_name or "").strip()
    domain = _registrable_domain(website)
    if not company_name or not domain:
        return "", ""

    session = session or build_session()
    try:
        # One call: top search hits + their intro extract + Wikidata id.
        resp = session.get(
            WIKI_API,
            params={
                "action": "query", "format": "json", "redirects": 1,
                "generator": "search", "gsrsearch": company_name, "gsrlimit": 3,
                "prop": "extracts|pageprops", "exintro": 1, "explaintext": 1,
                "ppprop": "wikibase_item",
            },
            timeout=TIMEOUT,
        )
        pages = (resp.json().get("query") or {}).get("pages") or {}
        # Search rank order (lower "index" = better match).
        for page in sorted(pages.values(), key=lambda p: p.get("index", 99)):
            qid = (page.get("pageprops") or {}).get("wikibase_item")
            extract = page.get("extract") or ""
            if not qid or not extract:
                continue
            if _wikidata_domain_matches(session, qid, domain):
                pageid = page.get("pageid")
                source = (f"https://en.wikipedia.org/?curid={pageid}"
                          if pageid else "https://en.wikipedia.org")
                return _trim(extract), source
        return "", ""
    except Exception:
        return "", ""
