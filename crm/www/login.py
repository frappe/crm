"""Branded login page for Tiberbu CRM.

Shadows Frappe's stock ``/login`` *page* only — it POSTs to the stock, unmodified
``/api/method/login`` whitelisted method, so the full auth contract (password, 2FA,
password-reset, social, LDAP) is preserved. We do NOT override the login/logout methods.

Server context mirrors Frappe's own ``www/login.py`` so behaviour (signup toggle,
user/pass toggle, email-link login, social providers, LDAP, open-redirect sanitization)
matches the desk login. Client JS (in login.html) handles every login response state,
including the ``verification`` + ``tmp_id`` 2FA flow (OTP App / SMS / Email).

context7-validated against /frappe/frappe version-16 ``auth.py`` + ``twofactor.py``:
login responses are "Logged In" (System User), "No App" (Website User), "Password Reset",
or ``{verification, tmp_id}`` when 2FA runs.
"""
from urllib.parse import urlparse

import frappe
from frappe import _
from frappe.apps import get_default_path
from frappe.utils import cint
from frappe.utils.data import escape_html
from frappe.utils.html_utils import get_icon_html
from frappe.utils.oauth import get_oauth2_authorize_url, get_oauth_keys
from frappe.utils.password import get_decrypted_password
from frappe.website.utils import get_home_page

from crm.branding import apply_brand_context, get_configured_app_brand

no_cache = True


def get_context(context):
	# Validate & sanitize redirect target (security critical).
	redirect_to = frappe.local.request.args.get("redirect-to")
	redirect_to = sanitize_redirect(redirect_to)

	# Already logged in -> bounce to target. Branch on user_type like native: Website Users
	# go to the website home page, not the SPA (which would 403 them).
	if frappe.session.user != "Guest":
		if not redirect_to:
			if frappe.session.data.user_type == "Website User":
				redirect_to = get_default_path() or get_home_page()
			else:
				redirect_to = get_default_path() or "/crm"
		if redirect_to != "login":
			frappe.local.flags.redirect_location = redirect_to
			raise frappe.Redirect

	brand = get_configured_app_brand()
	context.no_cache = 1
	context.no_header = True
	context.no_breadcrumbs = True
	context.title = _("Sign In - {0}").format(brand["app_name"])
	apply_brand_context(context, brand, surface="login")

	# Auth settings consumed by the template (mirror stock login).
	context.disable_user_pass_login = cint(frappe.get_system_settings("disable_user_pass_login")) or 0

	# Login label — Email first, matching native order.
	login_label = [_("Email")]
	if cint(frappe.get_system_settings("allow_login_using_mobile_number")):
		login_label.append(_("Mobile"))
	if cint(frappe.get_system_settings("allow_login_using_user_name")):
		login_label.append(_("Username"))
	context.login_label = f" {_('or')} ".join(login_label)

	context.login_with_email_link = frappe.get_system_settings("login_with_email_link")

	# In a provider-side OIDC authorize flow, suppress social buttons by policy.
	is_oidc_flow = _is_oidc_authorize_redirect(redirect_to)
	context.provider_logins = [] if is_oidc_flow else _build_provider_logins(redirect_to or "/crm")
	context.social_login = bool(context.provider_logins)

	context.redirect_to = redirect_to or "/crm"
	# CSRF token for the guest session (generating it is what makes /api/method/login
	# accept the POST from this page; see frappe auth.LoginManager.validate_csrf_token).
	context.csrf_token = frappe.sessions.get_csrf_token()
	return context


def _is_oidc_authorize_redirect(redirect_to: str | None) -> bool:
	if not redirect_to:
		return False
	return "/api/method/frappe.integrations.oauth2.authorize" in redirect_to


def _build_provider_logins(redirect_to: str) -> list[dict]:
	"""Return a list of {provider_name, auth_url, icon} dicts for enabled Social Login Keys.

	Uses frappe.get_all() matching native frappe/www/login.py — this page runs as Guest
	and Social Login Key is System Manager-only, so get_all() (no permission check) is correct.
	Icon HTML is built server-side so the template renders it with | safe.
	"""
	providers = frappe.get_all(
		"Social Login Key",
		filters={"enable_social_login": 1},
		fields=["name", "provider_name", "client_id", "base_url", "icon"],
		order_by="name",
	)
	result = []
	for p in providers:
		client_secret = get_decrypted_password(
			"Social Login Key", p.name, "client_secret", raise_exception=False
		)
		if not client_secret:
			continue

		icon = None
		if p.icon:
			if p.provider_name == "Custom":
				icon = get_icon_html(p.icon, small=True)
			else:
				icon = f"<img src={escape_html(p.icon)!r} alt={escape_html(p.provider_name)!r}>"

		if p.client_id and p.base_url and get_oauth_keys(p.name):
			try:
				auth_url = get_oauth2_authorize_url(p.name, redirect_to)
			except Exception:
				continue
			result.append(
				{
					"provider_name": p.provider_name,
					"auth_url": auth_url,
					"icon": icon,
				}
			)
	return result


def sanitize_redirect(redirect: str | None) -> str | None:
	"""Allow same-host redirects only; reject cross-origin. Mirrors native frappe/www/login.py."""
	if not redirect:
		return redirect

	parsed_redirect = urlparse(redirect)
	parsed_request_host = urlparse(frappe.local.request.url)
	output_parsed_url = parsed_redirect._replace(
		netloc=parsed_request_host.netloc, scheme=parsed_request_host.scheme
	)
	if parsed_redirect.netloc:
		if parsed_request_host.netloc != parsed_redirect.netloc:
			output_parsed_url = output_parsed_url._replace(path="/crm")
		else:
			output_parsed_url = output_parsed_url._replace(path=parsed_redirect.path)

	return output_parsed_url.geturl()
