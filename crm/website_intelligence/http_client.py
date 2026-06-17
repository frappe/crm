"""Thin, defensive HTTP layer.

Handles timeouts, retries, oversized responses and non-HTML content types so the
crawler never hangs or blows up on a broken site. Exposes a tiny surface
(`fetch`) that returns `(status_code, html, error)`.
"""

from __future__ import annotations

import requests
from requests.adapters import HTTPAdapter

try:  # urllib3 ships with requests; guard the import path across versions.
    from urllib3.util.retry import Retry
except Exception:  # pragma: no cover
    Retry = None


DEFAULT_TIMEOUT = 10            # seconds, per request
MAX_BYTES = 3_000_000          # ignore anything larger than ~3 MB
USER_AGENT = (
    "Mozilla/5.0 (compatible; FrappeCRM-WebsiteIntelligence/1.0; "
    "+https://frappe.io/crm)"
)
HTML_CONTENT_TYPES = ("text/html", "application/xhtml")


def build_session(retries: int = 2) -> requests.Session:
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }
    )
    if Retry is not None:
        retry = Retry(
            total=retries,
            backoff_factor=0.3,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=frozenset(["GET", "HEAD"]),
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
    return session


def fetch(url: str, session: requests.Session | None = None,
          timeout: int = DEFAULT_TIMEOUT):
    """Fetch a URL and return (status_code, html, error).

    Never raises — any failure is reported as a non-empty `error` string with a
    status_code of 0. Non-HTML responses are skipped (returned with empty html).
    """
    own_session = session is None
    session = session or build_session()
    try:
        resp = session.get(
            url, timeout=timeout, allow_redirects=True, stream=True
        )
        content_type = resp.headers.get("Content-Type", "").lower()
        if content_type and not any(ct in content_type for ct in HTML_CONTENT_TYPES):
            resp.close()
            return resp.status_code, "", f"skipped non-HTML content-type: {content_type}"

        # Read at most MAX_BYTES to avoid memory blowups on huge pages.
        chunks = []
        total = 0
        for chunk in resp.iter_content(chunk_size=16_384, decode_unicode=False):
            if not chunk:
                continue
            total += len(chunk)
            chunks.append(chunk)
            if total >= MAX_BYTES:
                break
        resp.close()

        encoding = resp.encoding or "utf-8"
        raw = b"".join(chunks)
        try:
            html = raw.decode(encoding, errors="replace")
        except (LookupError, TypeError):
            html = raw.decode("utf-8", errors="replace")
        return resp.status_code, html, ""
    except requests.exceptions.Timeout:
        return 0, "", f"timeout after {timeout}s"
    except requests.exceptions.TooManyRedirects:
        return 0, "", "too many redirects"
    except requests.exceptions.SSLError as exc:
        return 0, "", f"ssl error: {exc}"
    except requests.exceptions.ConnectionError as exc:
        return 0, "", f"connection error: {exc}"
    except requests.exceptions.RequestException as exc:
        return 0, "", f"request error: {exc}"
    except Exception as exc:  # pragma: no cover - last-resort guard
        return 0, "", f"unexpected error: {exc}"
    finally:
        if own_session:
            session.close()
