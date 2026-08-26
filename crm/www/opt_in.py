"""
crm/www/opt-in.py — Guest-accessible Self Opt-In Portal shell.

Serves the compiled Vue opt-in wizard at /opt-in. The <script>/<link> asset tags
(JS bundle, module preloads AND the stylesheet) are lifted verbatim from the
Vite-built crm/public/frontend/opt-in.html so the shell always matches the current
build — hashes change on every `yarn build`, so hard-coding them (or globbing only
the JS) leaves the page unstyled. Excludes the PWA service-worker/manifest tags:
a guest, one-shot portal has no use for offline caching.
"""
import os

import frappe
import frappe.sessions  # ensure frappe.sessions is resolvable for get_csrf_token()

no_cache = 1
base_template_path = ""  # Render standalone — no Frappe nav/header wrapper

_BUILT_HTML = ("public", "frontend", "opt-in.html")


def get_context(context):
    context.optin_network = frappe.form_dict.get("network") or ""
    # Guest portal, but a logged-in operator opening it in the same browser hits
    # CSRF enforcement — inject the token so frappe-ui POSTs don't 400.
    context.csrf_token = frappe.sessions.get_csrf_token()
    context.optin_head = _asset_head()
    return context


def _asset_head():
    """Extract module-script, modulepreload and stylesheet tags from the built HTML."""
    path = os.path.join(frappe.get_app_path("crm"), *_BUILT_HTML)
    try:
        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except OSError:
        frappe.log_error("opt-in shell: built asset HTML not found at " + path)
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
