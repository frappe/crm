"""Shared branding helper for Tiberbu CRM public (Jinja `www/`) surfaces.

Reads the runtime brand from the existing **FCRM Settings** Single doctype (populated
in E1-S3: `brand_name`, `brand_logo`, `favicon`) and exposes it to the branded login /
landing / access-restricted pages. Everything degrades to module-level defaults when a
field is empty, so a brand-less install still renders.

Fork-safety: this is a NEW additive module — it does not edit any upstream file. The only
core touch-points are the `www/` pages and the `hooks.py` wiring (E2-S1), both additive.
"""
import frappe

# Interim Tiberbu identity (BRD watch-out: swap for official SVG + canonical hex when
# brand delivers). #BC1823 = Tiberbu primary red from tiberbu.com.
DEFAULT_APP_NAME = "Tiberbu CRM"
DEFAULT_TAGLINE = "Powering Better Health"
DEFAULT_BRAND_LOGO = "/assets/crm/images/tiberbu-mark.svg"
DEFAULT_FAVICON = "/assets/crm/images/tiberbu-mark.svg"
BRAND_PRIMARY = "#bc1823"
BRAND_PRIMARY_DARK = "#8f111b"
# Where a signed-in user belongs (the SPA). Single source of truth for redirects.
APP_HOME_ROUTE = "/crm"


def _clean(value):
	"""Trim strings; treat empty/whitespace as unset so defaults apply."""
	if isinstance(value, str):
		value = value.strip()
	return value or None


def get_brand_initials(app_name: str) -> str:
	"""Two-letter fallback mark from the app name (e.g. 'Tiberbu CRM' -> 'TC')."""
	words = [w for w in (app_name or "").split() if w]
	if not words:
		return "TC"
	if len(words) == 1:
		return words[0][:2].upper()
	return (words[0][0] + words[-1][0]).upper()


def get_configured_app_brand() -> dict:
	"""Return a normalized brand dict, reading FCRM Settings with safe fallbacks.

	Never raises — a failure to read settings degrades to module defaults so the auth /
	landing surfaces always render (they run in the request-render pipeline).
	"""
	app_name = logo = favicon = None
	try:
		# get_cached_value avoids a full doc load on every guest request.
		app_name, logo, favicon = frappe.db.get_value(
			"FCRM Settings",
			"FCRM Settings",
			["brand_name", "brand_logo", "favicon"],
		) or (None, None, None)
	except Exception:
		pass

	app_name = _clean(app_name) or DEFAULT_APP_NAME
	return {
		"app_name": app_name,
		"logo": _clean(logo) or DEFAULT_BRAND_LOGO,
		"favicon": _clean(favicon) or DEFAULT_FAVICON,
		"initials": get_brand_initials(app_name),
		"tagline": DEFAULT_TAGLINE,
		"primary": BRAND_PRIMARY,
		"primary_dark": BRAND_PRIMARY_DARK,
		"home_route": APP_HOME_ROUTE,
	}


def apply_brand_context(context, brand: dict, *, surface: str = "default"):
	"""Attach normalized brand values to a Jinja page `context`.

	`surface` is accepted for parity with the reference implementation / future
	per-surface asset selection; all surfaces currently share the one mark.
	"""
	context.app_name = brand["app_name"]
	context.brand_logo = brand["logo"]
	context.logo = brand["logo"]
	context.favicon = brand["favicon"]
	context.brand_initials = brand["initials"]
	context.tagline = brand["tagline"]
	context.brand_primary = brand["primary"]
	context.brand_primary_dark = brand["primary_dark"]
	context.home_route = brand["home_route"]
	context.brand_surface = surface
	context.brand = brand
	return context
