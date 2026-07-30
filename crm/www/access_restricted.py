"""Branded "Access Restricted" page for users blocked from Frappe Desk.

Rendered when the desk route guard (``crm.api.route_guard``) redirects a
non-allow-listed user away from ``/app`` / ``/desk``.

Route note: this ``.py`` file (underscore) pairs with ``access-restricted.html``
(hyphen). Frappe's ``www/`` auto-router serves the route from the HTML filename, so the
URL is ``/access-restricted`` — matching ``UNAUTHORIZED_ROUTE`` in the guard, and sharing
NO prefix with ``/app``/``/desk`` (redirect-loop safety).
"""
import frappe

no_cache = True


def get_context(context):
	# Defense-in-depth: this page is only meaningful for a blocked, authenticated
	# non-admin. Redirect the two users who should never *see* it.
	user = frappe.session.user
	if user == "Administrator":
		# An admin is never blocked — send them to Desk.
		frappe.local.flags.redirect_location = "/app"
		raise frappe.Redirect
	if not user or user == "Guest":
		# Not authenticated yet — let them log in.
		frappe.local.flags.redirect_location = "/login"
		raise frappe.Redirect

	context.no_cache = 1
	context.no_header = True
	context.no_breadcrumbs = True
	# CSRF token so the "Sign out" button can POST to the (POST-only) logout method.
	context.csrf_token = frappe.sessions.get_csrf_token()

	# Branding is optional — guard it so a brand-less copy still renders the page.
	try:
		from crm.branding import apply_brand_context, get_configured_app_brand

		brand = get_configured_app_brand()
		apply_brand_context(context, brand, surface="splash")
		context.title = f"Access Restricted - {brand['app_name']}"
	except Exception:
		context.title = "Access Restricted"
		context.app_name = "Tiberbu CRM"
		context.brand_logo = "/assets/crm/images/tiberbu-mark.svg"
		context.brand_primary = "#bc1823"
		context.brand_primary_dark = "#8f111b"
		context.home_route = "/crm"

	return context
