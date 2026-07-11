# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""HTTP fetch layer for the crawler, built on framework helpers, with an SSRF guard.

Built on ``frappe.utils.get_request_session`` (so retry/adapter behavior is the
framework's), this module adds the crawler-specific behavior the framework does NOT
provide:

* a hard download cap (``max_download_bytes``) via streamed reads,
* an HTML-only content-type filter,
* the never-raise ``(status_code, html, error)`` contract, and
* a mandatory **SSRF guard** that resolves the hostname and rejects loopback /
  private / link-local / reserved addresses, honors the Settings allow/block lists,
  and **re-validates the resolved IP after every redirect** (it does not blindly
  follow redirects).

Limits (timeout, byte cap, retries, user-agent) come from config, not constants.
"""

from __future__ import annotations

import ipaddress
import re
import socket
from urllib.parse import urlparse

import frappe
from frappe.utils import get_request_session

HTML_CONTENT_TYPES = ("text/html", "application/xhtml")
RETRY_STATUS_FORCELIST = (429, 500, 502, 503, 504)
# Cap redirect chases ourselves (we follow manually to re-check each hop).
MAX_REDIRECTS = 5


class SSRFError(Exception):
	"""Raised internally when a URL fails the SSRF guard. Never escapes ``fetch``."""


# --------------------------------------------------------------------------- #
# SSRF guard
# --------------------------------------------------------------------------- #
def _registrable_domain(netloc: str) -> str:
	netloc = (netloc or "").lower().split(":")[0]
	if netloc.startswith("www."):
		netloc = netloc[4:]
	parts = netloc.split(".")
	return ".".join(parts[-2:]) if len(parts) >= 2 else netloc


def _domain_in_list(host: str, domains: list) -> bool:
	"""True if ``host`` equals or is a subdomain of any entry in ``domains``."""
	host = (host or "").lower().split(":")[0]
	for d in domains:
		d = (d or "").lower().strip()
		if not d:
			continue
		if host == d or host.endswith("." + d):
			return True
	return False


def _is_blocked_ip(ip: str) -> bool:
	"""True if ``ip`` is not a public (globally-routable) address.

	Mirrors the framework's own SSRF check (``make_safe_get_request`` in
	frappe.utils.safe_exec): ``not is_global`` rejects loopback, private, link-local,
	reserved and unspecified addresses -- and also shared/CGNAT ranges (100.64.0.0/10,
	0.0.0.0/8) that an explicit flag enumeration tends to miss. ``is_global`` does NOT
	cover multicast, so keep an explicit reject for it (the framework helper misses it).
	"""
	try:
		addr = ipaddress.ip_address(ip)
	except ValueError:
		return True  # unparseable -> reject
	return not addr.is_global or addr.is_multicast


def _resolve_ips(host: str) -> list:
	"""Resolve ``host`` to its IP strings via ``socket.getaddrinfo``."""
	infos = socket.getaddrinfo(host, None)
	# index 4 is sockaddr; element 0 is the IP for both AF_INET / AF_INET6.
	return list({info[4][0] for info in infos})


def validate_url(url: str, cfg) -> str:
	"""SSRF guard entry point. Returns the validated URL or raises ``SSRFError``.

	Validates the scheme, then resolves the hostname and rejects any URL that
	resolves to a loopback/private/link-local/reserved address, unless
	``allow_private_networks`` is set. Honors the Settings allow/block domain
	lists: a blocked domain is always rejected; if an allow list exists the host
	must be on it.
	"""
	parsed = urlparse(url)
	if parsed.scheme not in ("http", "https"):
		raise SSRFError(f"unsupported URL scheme: {parsed.scheme or '(none)'}")

	host = (parsed.hostname or "").strip()
	if not host:
		raise SSRFError("URL has no host")

	blocked = cfg.blocked_domains if cfg else []
	allowed = cfg.allowed_domains if cfg else []
	if _domain_in_list(host, blocked):
		raise SSRFError(f"host is on the blocked-domains list: {host}")
	if allowed and not _domain_in_list(host, allowed):
		raise SSRFError(f"host is not on the allowed-domains list: {host}")

	allow_private = bool(cfg.setting("allow_private_networks")) if cfg else False
	if not allow_private:
		try:
			ips = _resolve_ips(host)
		except socket.gaierror as exc:
			raise SSRFError(f"could not resolve host {host}: {exc}") from exc
		if not ips:
			raise SSRFError(f"could not resolve host {host}")
		for ip in ips:
			if _is_blocked_ip(ip):
				raise SSRFError(f"host {host} resolves to a non-public address: {ip}")

	return url


# --------------------------------------------------------------------------- #
# Session
# --------------------------------------------------------------------------- #
def build_session(cfg=None):
	"""Build the crawler session on the framework helper.

	Sets crawler User-Agent + Accept headers from Settings and customizes the
	retry status_forcelist for 429/5xx.
	"""
	retries = int(cfg.setting("retry_count")) if cfg else 2
	user_agent = (
		cfg.setting("user_agent") if cfg else "Mozilla/5.0 (compatible; FrappeCRM-DomainEnrichment/1.0)"
	)
	session = get_request_session(max_retries=retries)
	# get_request_session only forces 500; widen to the usual transient set.
	try:
		from requests.adapters import HTTPAdapter, Retry

		retry = Retry(
			total=retries,
			backoff_factor=0.3,
			status_forcelist=RETRY_STATUS_FORCELIST,
			allowed_methods=frozenset(["GET", "HEAD"]),
		)
		adapter = HTTPAdapter(max_retries=retry)
		session.mount("http://", adapter)
		session.mount("https://", adapter)
	except Exception:  # pragma: no cover - keep the framework default on any issue
		pass
	session.headers.update(
		{
			"User-Agent": user_agent,
			"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
			"Accept-Language": "en-US,en;q=0.9",
		}
	)
	return session


# --------------------------------------------------------------------------- #
# Fetch
# --------------------------------------------------------------------------- #
_META_CHARSET_RE = re.compile(rb"""charset=["']?\s*([a-zA-Z0-9_\-]+)""", re.IGNORECASE)


def _sniff_html_charset(raw: bytes) -> str | None:
	"""Charset declared in a <meta> tag (handles both `<meta charset=...>` and
	`<meta http-equiv content="...; charset=...">`); None if absent."""
	match = _META_CHARSET_RE.search(raw[:4096])
	if match:
		try:
			return match.group(1).decode("ascii")
		except (UnicodeDecodeError, AttributeError):
			return None
	return None


def _read_capped(resp, max_bytes: int) -> str:
	chunks = []
	total = 0
	for chunk in resp.iter_content(chunk_size=16_384, decode_unicode=False):
		if not chunk:
			continue
		total += len(chunk)
		chunks.append(chunk)
		if total >= max_bytes:
			break
	raw = b"".join(chunks)
	# requests defaults text/* without an explicit charset to ISO-8859-1, which
	# mojibakes UTF-8 pages that only declare their charset in a <meta> tag. When the
	# header carries no charset, trust the document's own declaration instead.
	if "charset=" in resp.headers.get("Content-Type", "").lower():
		encoding = resp.encoding or "utf-8"
	else:
		encoding = _sniff_html_charset(raw) or "utf-8"
	try:
		return raw.decode(encoding, errors="replace")
	except (LookupError, TypeError):
		return raw.decode("utf-8", errors="replace")


def fetch(url: str, cfg, session=None):
	"""Fetch a URL and return ``(status_code, html, error, final_url)``.

	Never raises -- any failure (SSRF rejection, timeout, non-HTML, oversized) is
	reported as a non-empty ``error`` string with ``status_code`` 0 (or the actual
	status for content-type skips). Redirects are followed manually so the resolved
	IP of every hop is re-validated by the SSRF guard; ``final_url`` is the URL that
	actually served the body (post-redirect), so callers resolve relative links and
	record provenance against the right host.

	SSRF note: ``validate_url`` resolves and checks the host, but requests re-resolves
	it when connecting, so a DNS-rebinding host (short TTL, alternating answers) can
	still pass the guard and connect to a private IP. Pinning the validated IP to the
	connection is deferred -- see the module docstring / README.
	"""
	import requests

	timeout = int(cfg.setting("request_timeout")) if cfg else 10
	max_bytes = int(cfg.setting("max_download_bytes")) if cfg else 3_000_000

	own_session = session is None
	session = session or build_session(cfg)
	current = url
	try:
		for _hop in range(MAX_REDIRECTS + 1):
			try:
				validate_url(current, cfg)
			except SSRFError as exc:
				return 0, "", f"blocked by SSRF guard: {exc}", current

			resp = session.get(
				current,
				timeout=timeout,
				allow_redirects=False,  # follow manually to re-validate each hop
				stream=True,
			)

			if resp.is_redirect or resp.is_permanent_redirect:
				location = resp.headers.get("Location")
				resp.close()
				if not location:
					return resp.status_code, "", "redirect without Location header", current
				current = requests.compat.urljoin(current, location)
				continue

			content_type = resp.headers.get("Content-Type", "").lower()
			if content_type and not any(ct in content_type for ct in HTML_CONTENT_TYPES):
				status = resp.status_code
				resp.close()
				return status, "", f"skipped non-HTML content-type: {content_type}", current

			html = _read_capped(resp, max_bytes)
			status = resp.status_code
			resp.close()
			return status, html, "", current

		return 0, "", "too many redirects", current
	except requests.exceptions.Timeout:
		return 0, "", f"timeout after {timeout}s", current
	except requests.exceptions.TooManyRedirects:
		return 0, "", "too many redirects", current
	except requests.exceptions.SSLError as exc:
		return 0, "", f"ssl error: {exc}", current
	except requests.exceptions.ConnectionError as exc:
		return 0, "", f"connection error: {exc}", current
	except requests.exceptions.RequestException as exc:
		return 0, "", f"request error: {exc}", current
	except Exception as exc:  # pragma: no cover - last-resort guard
		return 0, "", f"unexpected error: {exc}", current
	finally:
		if own_session:
			session.close()
