"""
crm/www/sign-contract.py — Public signing portal for CRM Contract signatories.
No authentication required — identity is proven by the OTP gate in the Vue SPA.

NOTE: Frappe imports the www controller by its Python-safe module name, so the
route /sign-contract loads THIS module (sign_contract.py, underscore), not the
hyphenated sibling. Keep both in sync.

Asset <script>/<link> tags (JS bundle, module preloads AND the stylesheet) are
lifted verbatim from the Vite-built crm/public/frontend/sign-contract.html so the
shell always matches the current build — hashes change on every `yarn build`, and
globbing only the JS leaves the page unstyled. PWA service-worker/manifest tags are
excluded: a guest, one-shot portal has no use for offline caching.
"""
import os

import frappe
import frappe.sessions  # ensure frappe.sessions is resolvable for get_csrf_token()

no_cache = 1
base_template_path = ""  # Render standalone — no Frappe nav/header wrapper

_BUILT_HTML = ("public", "frontend", "sign-contract.html")


def get_context(context):
    fd = frappe.form_dict
    context.sc_contract = fd.get("contract") or ""
    context.sc_role = fd.get("role") or ""
    context.sc_token = fd.get("token") or ""
    # Guest portal, but the issuer often opens the link while logged into the CRM
    # in the same browser — that session enforces CSRF, so the token MUST be
    # injected or frappe-ui POSTs (request_otp/verify_otp/sign) fail with CSRFTokenError.
    context.csrf_token = frappe.sessions.get_csrf_token()
    context.signing_head = _asset_head()
    return context


def _asset_head():
    """Extract module-script, modulepreload and stylesheet tags from the built HTML."""
    path = os.path.join(frappe.get_app_path("crm"), *_BUILT_HTML)
    try:
        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except OSError:
        frappe.log_error("sign-contract shell: built asset HTML not found at " + path)
        return ""

    kept = []
    for line in lines:
        tag = line.strip()
        if any(skip in tag for skip in ("registerSW", "vite-plugin-pwa", 'rel="manifest"')):
            continue
        if (
            tag.startswith('<script type="module"')
            or tag.startswith('<link rel="modulepreload"')
            or tag.startswith('<link rel="stylesheet"')
        ):
            kept.append(tag)
    return "\n    ".join(kept)
