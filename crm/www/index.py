"""Public landing page for Tiberbu CRM (site root, set via `home_page = "index"`).

Guests see the branded splash; logged-in users are redirected to the SPA (`/crm`).

Root-resolution note: `home_page = "index"` alone is NOT enough — Frappe's
`get_home_page()` still resolves '/' to a System User's `default_workspace`
(`/desk/<workspace>`) before this page runs. The `pin_home_page_to_landing`
`before_request` hook (crm/api/route_guard.py) forces '/' -> index on every request so
this redirect actually runs for workspace-having users, closing a desk-fence bypass.
"""
import frappe
from frappe import _

from crm.branding import apply_brand_context, get_configured_app_brand

no_cache = True


def get_context(context):
	# Logged-in users belong in the app, not on the marketing splash.
	if frappe.session.user != "Guest":
		frappe.local.flags.redirect_location = "/crm"
		raise frappe.Redirect

	brand = get_configured_app_brand()
	context.no_cache = 1
	context.no_header = True
	context.no_breadcrumbs = True
	context.title = _("{0} - {1}").format(brand["app_name"], brand["tagline"])
	apply_brand_context(context, brand, surface="splash")

	# Primary CTA (E3-S2): "Request a Demo" -> the public CRM form that creates a real
	# CRM Lead via the native Web Form engine (crm/www/crm_form.py + crm/api/form.py).
	# Falls back to /login if an admin hasn't published the form yet.
	context.cta_text = "Request a Demo"
	context.cta_link = _demo_form_route()
	context.cta_secondary_text = "Sign In"
	context.cta_secondary_link = "/login"

	context.features = [
		{
			"title": "Unified Patient Relationships",
			"description": "One record for every lead, referral, and patient interaction across the Careverse HMIS.",
		},
		{
			"title": "Sales & Referral Pipelines",
			"description": "Track deals, referral sources, and follow-ups with a pipeline built for healthcare growth.",
		},
		{
			"title": "Integrated Telephony",
			"description": "Click-to-call, screen-pop, and call logging — inbound and outbound — from within the CRM.",
		},
		{
			"title": "Support Automation",
			"description": "SLAs, assignment rules, and onboarding journeys keep every patient and partner cared for.",
		},
	]

	return context


def _demo_form_route() -> str:
	"""Route to the published 'Request a Demo' CRM form, or /login if none is published.

	Matches any published FCRM Web Form targeting CRM Lead (route defaults to
	'request-a-demo'); degrades to /login so the CTA is never a dead link.
	"""
	try:
		route = frappe.db.get_value(
			"Web Form",
			{"module": "FCRM", "doc_type": "CRM Lead", "crm_published": 1},
			"route",
		)
		if route:
			return f"/crm-form/{route}"
	except Exception:
		pass
	return "/login"
