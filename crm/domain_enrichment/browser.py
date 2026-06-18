# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Chromium render fallback for JavaScript-rendered pages.

A **background-job-only** helper that renders a single URL with Frappe's bundled
headless-Chromium + CDP stack (``frappe.utils.chromium``) and returns the fully
rendered DOM. The crawler calls it ONLY when a page comes back JS-empty and the
admin has enabled ``render_js``. Modeled on ``frappe.utils.preview.capture_screenshot``.

This is a *renderer*, not a crawler: it navigates one URL and returns
``(status, html, error)``, mirroring ``http.fetch``'s never-raise contract. The
SSRF guard (``http.validate_url``) runs before any navigation, and the helper
refuses to launch inside a web-request context, so a browser can never be spun up
behind a request spinner.
"""

from __future__ import annotations

import frappe

from .http import SSRFError, validate_url

DEFAULT_MAX_BYTES = 3_000_000
# networkIdle lets client-side frameworks finish rendering before we read the DOM.
RENDER_WAIT = ["load", "DOMContentLoaded", "networkIdle"]


def _in_web_request() -> bool:
	"""True if we're serving an HTTP request (vs running in a background worker)."""
	return getattr(frappe.local, "request", None) is not None


def _safe(fn):
	if fn:
		try:
			fn()
		except Exception:
			pass


def render(url: str, cfg=None) -> tuple[int, str, str]:
	"""Render ``url`` in headless Chromium; return ``(status, html, error)``.

	Never raises. Returns an error tuple (and launches nothing) when: we're in a
	web-request context, the SSRF guard rejects the URL, Chromium isn't provisioned
	(``bench setup-chromium``), or any CDP error occurs. On success returns
	``(200, rendered_outer_html, "")`` with the HTML capped to ``max_download_bytes``.
	"""
	if _in_web_request():
		return 0, "", "chromium render is background-job only"

	try:
		validate_url(url, cfg)
	except SSRFError as exc:
		return 0, "", f"blocked by SSRF guard: {exc}"

	max_bytes = int(cfg.setting("max_download_bytes")) if cfg else DEFAULT_MAX_BYTES
	user_agent = (cfg.setting("user_agent") if cfg else "") or ""

	try:
		from frappe.utils.chromium import CDPSocketClient, ChromiumManager, Page
	except Exception as exc:
		return 0, "", f"chromium stack unavailable: {exc}"

	generator = ChromiumManager()
	browser_id = frappe.utils.random_string(10)
	generator.add_browser(browser_id)
	session = page = None
	try:
		try:
			if not generator._devtools_url:
				generator._set_devtools_url()
			session = CDPSocketClient(generator._devtools_url)
			session.connect()
			context, error = session.send("Target.createBrowserContext", {"disposeOnDetach": True})
			if error:
				return 0, "", f"chromium context error: {error}"

			page = Page(session, context["browserContextId"], "scrape")
			page.is_print_designer = False  # normally set by Browser.new_page
			page.set_media_emulation("screen")  # Page defaults to print media
			if user_agent:
				page.send("Network.enable")
				page.send("Network.setUserAgentOverride", {"userAgent": user_agent})

			page.navigate(url, wait_for=RENDER_WAIT)
			result = page.evaluate("document.documentElement.outerHTML")
			html = ((result or {}).get("result") or {}).get("value") or ""
			return 200, html[:max_bytes], ""
		finally:
			_safe(page and page.close)
			_safe(session and session.disconnect)
			generator.remove_browser(browser_id)
	except Exception:
		generator._close_browser()  # crashed chrome -> drop the poisoned singleton
		frappe.log_error(
			title="Domain Enrichment: chromium render failed",
			message=frappe.get_traceback(),
		)
		return 0, "", "chromium render error"
