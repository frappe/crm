# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""HTTP client for the CPF.CNPJ registry API.

One responsibility: ``GET {BASE_URL}/{token}/{package}/{document}``, parse the JSON,
and either return the payload (HTTP 200 and ``status == 1``) or raise
``RegistryLookupError(code, message)`` carrying the API ``erroCodigo``. The host is
fixed (a single public API endpoint), so there is no SSRF surface and no allow-list.

The token is a paid credential and lives only in the URL path: it is never written to
a log. Everything handed to ``frappe.log_error`` passes through ``_mask`` first, so the
token is replaced with ``***`` even when it surfaces inside a raw traceback or an
exception string (``requests`` embeds the failing URL in its exceptions).

Responses are read defensively: redirects are not followed (the host is fixed, so a
redirect can only be a misconfiguration or a probe), the body is streamed with a hard
size cap, and only then parsed as JSON.
"""

from __future__ import annotations

import json

import frappe
from frappe import _

BASE_URL = "https://api.cpfcnpj.com.br"
DEFAULT_TIMEOUT = 15
# Supported per-request timeout band. Settings.validate enforces it on save; the clamp in
# fetch is a defensive net so a stale or raw value can never make a call fail outright or
# pin a worker far beyond the intended limit.
MIN_TIMEOUT = 1
MAX_TIMEOUT = 60

# Hard cap on the response body we will read (1 MiB). A real package-6 payload is a few
# KiB; anything larger is a misbehaving endpoint or a probe, so we stop reading and fail
# rather than buffer an unbounded body into memory.
MAX_RESPONSE_BYTES = 1024 * 1024

# erroCodigo values that mean "the caller's document is wrong" (a user-fixable input),
# kept apart from transversal account/quota/rate errors so callers can react per class.
DOCUMENT_ERROR_CODES = frozenset({100, 101, 102, 200, 201, 202, 400})

# Human, English messages per erroCodigo. The API's own ``erro`` is Portuguese; these
# translate the operationally relevant ones. Falls back to the API message otherwise.
ERROR_MESSAGES = {
	100: "Invalid CPF (check digits do not match).",
	101: "Inform a CPF with 11 digits.",
	102: "The informed CPF does not exist in the registry.",
	200: "Invalid CNPJ (check digits do not match).",
	201: "Inform a CNPJ with 14 digits.",
	202: "The informed CNPJ does not exist in the registry.",
	400: "Malformed request parameters.",
	1000: "The API token is not authorized for this server's IP address.",
	1001: "Insufficient credits on the query package.",
	1002: "The account is suspended or inactive.",
	1003: "The IP and token are temporarily blacklisted.",
	1004: "The requested package is unavailable.",
	1005: "The query could not be completed on this package.",
	1006: "The registry service is temporarily unavailable.",
	1007: "Rate limit exceeded (too many requests per second).",
	1009: "This package requires commercial release.",
}


class _ResponseTooLarge(Exception):
	"""Internal: the response body exceeded ``MAX_RESPONSE_BYTES``. Never escapes
	``fetch`` -- it is translated into a transport-class ``RegistryLookupError``."""


class RegistryLookupError(Exception):
	"""A CPF.CNPJ lookup that did not return usable data.

	``code`` is the API ``erroCodigo`` (or ``0`` when the transport itself failed
	before any JSON was returned); ``message`` is a human, English description.
	"""

	def __init__(self, code: int, message: str):
		self.code = int(code or 0)
		self.message = message
		super().__init__(f"[{self.code}] {message}")

	@property
	def is_document_error(self) -> bool:
		"""True when the failure is a bad document (user-fixable), not an account/quota
		or transport problem."""
		return self.code in DOCUMENT_ERROR_CODES


def _session():
	"""A configured ``requests`` session, preferring the framework helper so retry /
	adapter behavior matches the rest of the app; falls back to a bare session on a
	framework build that does not ship it."""
	try:
		return frappe.utils.get_request_session()
	except Exception:
		import requests

		return requests.Session()


def _safe_url(package: int, document: str) -> str:
	"""The request URL with the token segment masked, safe to put in a log."""
	return f"{BASE_URL}/***/{package}/{document}"


def _mask(text: str, token: str) -> str:
	"""Replace every occurrence of ``token`` in ``text`` with ``***``.

	The last-line defense before any string reaches ``frappe.log_error``: a raw
	traceback or a ``requests`` exception can embed the full request URL (token and
	all), so the token is scrubbed out regardless of where in the string it appears.
	"""
	text = frappe.utils.cstr(text)
	if token:
		text = text.replace(token, "***")
	return text


def _read_capped(response, max_bytes: int) -> bytes:
	"""Stream the response body, stopping at ``max_bytes``.

	Raises ``_ResponseTooLarge`` the moment the accumulated size would exceed the cap,
	so an unbounded or hostile endpoint can never buffer more than ``max_bytes`` into
	memory. Returns the raw bytes (decoding is the caller's concern)."""
	chunks = []
	total = 0
	for chunk in response.iter_content(chunk_size=16_384, decode_unicode=False):
		if not chunk:
			continue
		total += len(chunk)
		if total > max_bytes:
			raise _ResponseTooLarge
		chunks.append(chunk)
	return b"".join(chunks)


def _message_for(code: int, api_message: str) -> str:
	"""Prefer the curated English message for ``code``; fall back to the API's own
	message, then to a generic line."""
	return ERROR_MESSAGES.get(int(code or 0)) or api_message or _("Registry lookup failed.")


def fetch(document: str, package: int, token: str, timeout: int = DEFAULT_TIMEOUT) -> dict:
	"""Look up ``document`` in ``package`` and return the parsed JSON payload.

	Raises ``RegistryLookupError`` when the HTTP status is not 200 or the payload
	carries ``status == 0``. The JSON body is read in every case (the API returns a
	structured ``erroCodigo`` even on HTTP 400), so the error class is always driven by
	the API code rather than the HTTP status alone.
	"""
	url = f"{BASE_URL}/{token}/{package}/{document}"
	timeout = max(MIN_TIMEOUT, min(int(timeout or DEFAULT_TIMEOUT), MAX_TIMEOUT))
	try:
		# allow_redirects=False: the host is fixed, so a redirect is never legitimate and
		# must not be chased. stream=True lets us cap the body before buffering it.
		response = _session().get(
			url,
			timeout=timeout,
			allow_redirects=False,
			stream=True,
		)
	except Exception as exc:
		# Transport failure before any JSON: log the traceback with the token masked and
		# surface a transport-class error (code 0).
		frappe.log_error(
			title="Registry Enrichment: request failed",
			message=_mask(f"{_safe_url(package, document)}\n{frappe.get_traceback()}", token),
		)
		raise RegistryLookupError(0, _("Could not reach the registry service.")) from exc

	try:
		raw = _read_capped(response, MAX_RESPONSE_BYTES)
	except _ResponseTooLarge as exc:
		frappe.log_error(
			title="Registry Enrichment: oversized response",
			message=f"{_safe_url(package, document)} -> HTTP {response.status_code}",
		)
		raise RegistryLookupError(0, _("The registry service returned an oversized response.")) from exc
	finally:
		response.close()

	try:
		payload = json.loads(raw.decode("utf-8", errors="replace"))
	except ValueError as exc:
		frappe.log_error(
			title="Registry Enrichment: non-JSON response",
			message=f"{_safe_url(package, document)} -> HTTP {response.status_code}",
		)
		raise RegistryLookupError(0, _("The registry service returned an invalid response.")) from exc

	if response.status_code != 200 or not payload.get("status"):
		code = payload.get("erroCodigo") or 0
		message = _message_for(code, payload.get("erro") or "")
		raise RegistryLookupError(code, message)

	return payload
