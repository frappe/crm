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
import re

import frappe
import frappe.sessions  # ensure frappe.sessions is resolvable for get_csrf_token()

no_cache = 1
base_template_path = ""  # Render standalone — no Frappe nav/header wrapper

_BUILT_HTML = ("public", "frontend", "sign-contract.html")

# Tiberbu red — used when the contract's network has no primary_colour set.
_DEFAULT_BRAND = "#bc1823"
_DEFAULT_BRAND_DARK = "#8f111b"
_HEX_RE = re.compile(r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")


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
    # The signing SPA styles every branded element via var(--brand-primary); if the
    # var is undefined the white-text primary buttons render white-on-white (invisible).
    # Resolve it from the contract's network so the page adopts network colours.
    brand, brand_dark = _brand_colours(context.sc_contract)
    context.brand_primary = brand
    context.brand_primary_dark = brand_dark
    return context


def _brand_colours(contract):
    """Resolve (primary, dark) hex colours from the contract's network.

    Falls back to Tiberbu red when the contract, network, or colour is missing,
    and strictly validates the stored value is a #hex literal before it reaches
    the inline <style> block (prevents CSS/markup injection via a doctype field).
    """
    colour = None
    if contract:
        try:
            slug = frappe.db.get_value("CRM Contract", contract, "network_slug")
            if slug:
                colour = frappe.db.get_value("CRM Opt-In Network", slug, "primary_colour")
        except Exception:
            colour = None  # never let branding lookup break the signing page

    colour = (colour or "").strip()
    if not _HEX_RE.match(colour):
        return _DEFAULT_BRAND, _DEFAULT_BRAND_DARK
    return colour, _darken(colour)


def _darken(hex_colour, factor=0.82):
    """Return hex_colour scaled toward black by `factor` (for :hover)."""
    h = hex_colour.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    try:
        r, g, b = (int(h[i : i + 2], 16) for i in (0, 2, 4))
    except ValueError:
        return _DEFAULT_BRAND_DARK
    r, g, b = (max(0, min(255, int(c * factor))) for c in (r, g, b))
    return "#%02x%02x%02x" % (r, g, b)


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
