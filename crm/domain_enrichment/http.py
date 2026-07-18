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
  follow redirects). Every connection is **pinned to the IP the guard validated**
  (Host header and TLS SNI/verification stay on the original hostname), so a
  DNS-rebinding host cannot pass validation with one address and connect to another.

Limits (timeout, byte cap, retries, user-agent) come from config, not constants.
"""

from __future__ import annotations

import ipaddress
import re
import socket
from urllib.parse import urlparse

import frappe
from frappe.utils import get_request_session
from requests.adapters import HTTPAdapter, Retry

HTML_CONTENT_TYPES = ("text/html", "application/xhtml")
RETRY_STATUS_FORCELIST = (429, 500, 502, 503, 504)
# Cap redirect chases ourselves (we follow manually to re-check each hop).
MAX_REDIRECTS = 5
# Default crawler UA: a current desktop-Chrome string so bot walls that reject bare
# clients serve HTML. Overridable via the CRM Enrichment Settings ``user_agent`` field.
DEFAULT_USER_AGENT = (
	"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
	"(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
)


class SSRFError(Exception):
	"""Raised internally when a URL fails the SSRF guard. Never escapes ``fetch``."""


# --------------------------------------------------------------------------- #
# SSRF guard
# --------------------------------------------------------------------------- #
def _domain_in_list(host: str, domains: list) -> bool:
	"""True if ``host`` equals or is a subdomain of any entry in ``domains``.

	The trailing dot of a fully-qualified name (``evil.com.``) is stripped from both
	sides -- it resolves identically in DNS, so leaving it on would let ``evil.com.``
	slip past a ``evil.com`` block/allow rule.
	"""
	host = (host or "").lower().split(":")[0].rstrip(".")
	for d in domains:
		d = (d or "").lower().strip().rstrip(".")
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
	resolves to a loopback/private/link-local/reserved address. Honors the
	Settings allow/block domain lists: a blocked domain is always rejected; if an
	allow list exists the host must be on it. The private-network rejection is
	unconditional -- there is no setting to disable it (that would be a pure SSRF
	footgun for a crawler that fetches user-supplied URLs).
	"""
	_validated_ips(url, cfg)
	return url


def _validated_ips(url: str, cfg) -> list:
	"""Run the full SSRF checks for ``url`` and return the resolved, validated IPs.

	The caller connects to one of these exact addresses (see ``_pinned_get``), so
	the IP that was checked is the IP that serves the request. Raises ``SSRFError``
	on any rejection.
	"""
	parsed = urlparse(url)
	if parsed.scheme not in ("http", "https"):
		raise SSRFError(f"unsupported URL scheme: {parsed.scheme or '(none)'}")

	# Strip the trailing dot of a fully-qualified name at the source, so the SAME
	# canonical host feeds the allow/block check AND DNS resolution -- ``evil.com.``
	# resolves identically to ``evil.com`` and must not bypass either.
	host = (parsed.hostname or "").strip().rstrip(".")
	if not host:
		raise SSRFError("URL has no host")

	blocked = cfg.blocked_domains if cfg else []
	allowed = cfg.allowed_domains if cfg else []
	if _domain_in_list(host, blocked):
		raise SSRFError(f"host is on the blocked-domains list: {host}")
	if allowed and not _domain_in_list(host, allowed):
		raise SSRFError(f"host is not on the allowed-domains list: {host}")

	try:
		ips = _resolve_ips(host)
	except socket.gaierror as exc:
		raise SSRFError(f"could not resolve host {host}: {exc}") from exc
	if not ips:
		raise SSRFError(f"could not resolve host {host}")
	for ip in ips:
		if _is_blocked_ip(ip):
			raise SSRFError(f"host {host} resolves to a non-public address: {ip}")

	# Deterministic order, IPv4 first: the caller pins the first entry, and unlike
	# requests' resolver it won't fall back across address families, so an IPv6
	# answer must not shadow a reachable IPv4 one on v4-only networks.
	return sorted(ips, key=lambda ip: (":" in ip, ip))


# --------------------------------------------------------------------------- #
# Session
# --------------------------------------------------------------------------- #
def build_session(cfg=None):
	"""Build the crawler session on the framework helper.

	Sets a browser-like header set (User-Agent from Settings + Accept / Sec-Fetch /
	client-hint headers a real browser sends) so servers that reject bare clients
	still serve HTML, and customizes the retry status_forcelist for 429/5xx. Note:
	this only spoofs headers -- the TLS fingerprint is still that of ``requests``
	(see the TLS note in CONTEXT.md).
	"""
	retries = int(cfg.setting("retry_count")) if cfg else 2
	user_agent = cfg.setting("user_agent") if cfg else DEFAULT_USER_AGENT
	session = get_request_session(max_retries=retries)
	# get_request_session only forces 500; widen to the usual transient set.
	try:
		adapter = HTTPAdapter(max_retries=_retry_policy(retries))
		session.mount("http://", adapter)
		session.mount("https://", adapter)
	except Exception:  # pragma: no cover - keep the framework default on any issue
		pass
	session.headers.update(
		{
			"User-Agent": user_agent,
			"Accept": (
				"text/html,application/xhtml+xml,application/xml;q=0.9,"
				"image/avif,image/webp,image/apng,*/*;q=0.8"
			),
			"Accept-Language": "en-US,en;q=0.9",
			# Browser-ish request context so bot walls that check these serve HTML.
			# (Accept-Encoding is left to requests so it only advertises codecs it can
			# actually decode.)
			"Upgrade-Insecure-Requests": "1",
			"Sec-Fetch-Dest": "document",
			"Sec-Fetch-Mode": "navigate",
			"Sec-Fetch-Site": "none",
			"Sec-Fetch-User": "?1",
			"Sec-CH-UA": '"Chromium";v="125", "Not.A/Brand";v="24", "Google Chrome";v="125"',
			"Sec-CH-UA-Mobile": "?0",
			"Sec-CH-UA-Platform": '"Windows"',
		}
	)
	return session


def _retry_policy(retries: int) -> Retry:
	return Retry(
		total=retries,
		backoff_factor=0.3,
		status_forcelist=RETRY_STATUS_FORCELIST,
		allowed_methods=frozenset(["GET", "HEAD"]),
	)


# --------------------------------------------------------------------------- #
# Pinned connections (DNS-rebinding defense)
# --------------------------------------------------------------------------- #
class _PinnedIPAdapter(HTTPAdapter):
	"""Transport adapter for URLs whose netloc was rewritten to a pre-validated IP.

	``server_hostname`` keeps TLS SNI on the original hostname, and urllib3 also
	matches the certificate against it (it falls back to ``server_hostname`` when
	``assert_hostname`` is unset), so pinning does not weaken TLS verification.
	urllib3 strips ``server_hostname`` for plain-HTTP pools, so the same adapter
	serves both schemes.
	"""

	def __init__(self, hostname: str, **kwargs):
		self._server_hostname = hostname
		super().__init__(**kwargs)

	def init_poolmanager(self, *args, **kwargs):
		kwargs["server_hostname"] = self._server_hostname
		super().init_poolmanager(*args, **kwargs)


def _pinned_adapter(session, hostname: str, retries: int) -> _PinnedIPAdapter:
	"""Per-hostname adapter cache on the session, so keep-alive pooling survives
	across the pages of a crawl instead of reconnecting for every request."""
	cache = getattr(session, "_pinned_adapters", None)
	if cache is None:
		cache = {}
		session._pinned_adapters = cache
	adapter = cache.get(hostname)
	if adapter is None:
		adapter = _PinnedIPAdapter(hostname, max_retries=_retry_policy(retries))
		cache[hostname] = adapter
	return adapter


def _pinned_get(session, url: str, pinned_ip: str, timeout: int, retries: int):
	"""GET ``url`` connecting to ``pinned_ip`` -- an address the SSRF guard just
	validated -- so a DNS answer that changes between validation and connection
	(rebinding) cannot steer the socket somewhere else. Only the socket target is
	rewritten: the Host header, TLS SNI and certificate verification all stay on
	the original hostname.
	"""
	import requests

	parsed = urlparse(url)
	host = parsed.hostname or ""
	ip_netloc = f"[{pinned_ip}]" if ":" in pinned_ip else pinned_ip
	if parsed.port:
		ip_netloc = f"{ip_netloc}:{parsed.port}"
	host_header = f"{host}:{parsed.port}" if parsed.port else host

	prepared = session.prepare_request(
		requests.Request(
			"GET",
			parsed._replace(netloc=ip_netloc).geturl(),
			headers={"Host": host_header},
		)
	)
	return _pinned_adapter(session, host, retries).send(
		prepared,
		timeout=timeout,
		stream=True,
		verify=session.verify,
		cert=session.cert,
	)


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


def fetch(url: str, cfg, session=None, html_only: bool = True):
	"""Fetch a URL and return ``(status_code, html, error, final_url)``.

	Never raises -- any failure (SSRF rejection, timeout, non-HTML, oversized) is
	reported as a non-empty ``error`` string with ``status_code`` 0 (or the actual
	status for content-type skips). Redirects are followed manually so the resolved
	IP of every hop is re-validated by the SSRF guard; ``final_url`` is the URL that
	actually served the body (post-redirect), so callers resolve relative links and
	record provenance against the right host. Pass ``html_only=False`` to accept
	non-HTML bodies (e.g. ``text/plain`` robots.txt).

	SSRF note: each hop connects to the exact IP the guard validated for it
	(``_pinned_get``), so a DNS-rebinding host (short TTL, alternating answers)
	cannot pass validation with a public address and serve the request from a
	private one.
	"""
	import requests

	timeout = int(cfg.setting("request_timeout")) if cfg else 10
	max_bytes = int(cfg.setting("max_download_bytes")) if cfg else 3_000_000
	retries = int(cfg.setting("retry_count")) if cfg else 2

	own_session = session is None
	session = session or build_session(cfg)
	current = url
	try:
		for _hop in range(MAX_REDIRECTS + 1):
			try:
				ips = _validated_ips(current, cfg)
			except SSRFError as exc:
				return 0, "", f"blocked by SSRF guard: {exc}", current

			# Redirects are followed manually (each hop re-validated and re-pinned).
			resp = _pinned_get(session, current, ips[0], timeout, retries)

			if resp.is_redirect or resp.is_permanent_redirect:
				location = resp.headers.get("Location")
				resp.close()
				if not location:
					return resp.status_code, "", "redirect without Location header", current
				current = requests.compat.urljoin(current, location)
				continue

			content_type = resp.headers.get("Content-Type", "").lower()
			if html_only and content_type and not any(ct in content_type for ct in HTML_CONTENT_TYPES):
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
