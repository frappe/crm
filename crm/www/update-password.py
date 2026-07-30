"""Branded password-reset / update page for Tiberbu CRM.

Shadows Frappe's stock ``/update-password`` *page* only. It POSTs to the unmodified
whitelisted ``frappe.core.doctype.user.user.update_password`` (new_password + reset key,
or old_password when signed in) — the reset logic, key validation, strength policy, and
post-reset login are all Frappe's. We only re-skin the page to match the branded login.

Reached from the login "Forgot password?" link and from an expired-password redirect
(``…/update-password?key=…&password_expired=true``) — the login redirect guard already
whitelists ``/update-password`` so the key survives.
"""
import frappe
import frappe.sessions  # ensure frappe.sessions is resolvable for get_csrf_token()
from frappe import _

from crm.branding import apply_brand_context, get_configured_app_brand

no_cache = 1


def get_context(context):
	context.no_cache = 1
	context.no_header = True
	context.no_breadcrumbs = True

	brand = get_configured_app_brand()
	apply_brand_context(context, brand, surface="login")
	context.title = _("Reset Password - {0}").format(brand["app_name"])

	# The reset key from the emailed link (blank when a signed-in user changes their own
	# password). Read from request args (form_dict isn't populated for www GETs); the
	# client also re-reads it from the URL as the source of truth.
	args = frappe.local.request.args if frappe.local.request else {}
	context.reset_key = args.get("key") or ""
	context.password_expired = args.get("password_expired") in ("true", "1", "yes")
	# Signed-in users (no key) must supply their current password.
	context.is_logged_in = frappe.session.user != "Guest"
	context.csrf_token = frappe.sessions.get_csrf_token()
	return context
