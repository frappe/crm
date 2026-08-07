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
from frappe.utils import cint
from frappe.utils.oauth import get_oauth2_authorize_url, get_oauth_keys
from frappe.utils.password import get_decrypted_password

from crm.branding import apply_brand_context, get_configured_app_brand

no_cache = True

# Redirect targets we accept post-login (open-redirect guard). ``/crm`` is home.
# ``/update-password`` is allowed so a forced/expired-password reset redirect keeps its key.
SAFE_REDIRECT_PREFIXES = ("/crm", "/app", "/desk", "/api", "/update-password")


def get_context(context):
	# Validate & sanitize redirect target (security critical).
	redirect_to = frappe.local.request.args.get("redirect-to")
	redirect_to = sanitize_redirect(redirect_to)

	# Already logged in -> bounce to target (default the SPA).
	if frappe.session.user != "Guest":
		frappe.local.flags.redirect_location = redirect_to or "/crm"
		raise frappe.Redirect

	brand = get_configured_app_brand()
	context.no_cache = 1
	context.no_header = True
	context.no_breadcrumbs = True
	context.title = _("Sign In - {0}").format(brand["app_name"])
	apply_brand_context(context, brand, surface="login")

	# Auth settings consumed by the template (mirror stock login).
	context.disable_user_pass_login = cint(frappe.get_system_settings("disable_user_pass_login")) or 0

	# Login label (Email / Username / Mobile) — same composition as stock.
	login_label = []
	if cint(frappe.get_system_settings("allow_login_using_mobile_number")):
		login_label.append(_("Mobile"))
	if cint(frappe.get_system_settings("allow_login_using_user_name")):
		login_label.append(_("Username"))
	login_label.append(_("Email"))
	context.login_label = f" {_('or')} ".join(login_label)

	# In a provider-side OIDC authorize flow, suppress social buttons by policy.
	is_oidc_flow = _is_oidc_authorize_redirect(redirect_to)
	context.provider_logins = [] if is_oidc_flow else _build_provider_logins(redirect_to or "/crm")

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

	Mirrors the devsecops dashboard pattern: query the DocType directly, validate that
	client_id + client_secret + base_url are all set, then call get_oauth2_authorize_url()
	to produce the actual OAuth authorize URL. get_oauth2_providers() is intentionally
	NOT used here — it returns an internal flow dict, not display-ready objects; iterating
	it in Jinja yields the dict keys (strings), not provider records, causing the
	"Login with No such element" bug.
	"""
	providers = frappe.get_list(
		"Social Login Key",
		filters={"enable_social_login": 1},
		fields=["name", "provider_name", "client_id", "base_url", "icon"],
		order_by="name",
		ignore_permissions=True,  # SYSTEM-INTERNAL: login page runs as Guest; Social Login Key is System Manager-only
	)
	result = []
	for p in providers:
		if not (p.client_id and p.base_url):
			continue
		if not get_oauth_keys(p.name):
			continue
		client_secret = get_decrypted_password(
			"Social Login Key", p.name, "client_secret", raise_exception=False
		)
		if not client_secret:
			continue
		try:
			auth_url = get_oauth2_authorize_url(p.name, redirect_to)
		except Exception:
			continue
		result.append(
			{
				"provider_name": p.provider_name,
				"auth_url": auth_url,
				"icon": p.icon or "",
			}
		)
	return result


def sanitize_redirect(redirect_url):
	"""Prevent open-redirect: force internal path, whitelist known-safe prefixes."""
	if not redirect_url:
		return None

	parsed_redirect = urlparse(redirect_url)
	parsed_request = urlparse(frappe.local.request.url)

	# Block cross-origin absolute URLs; keep only the path for same-origin ones.
	if parsed_redirect.scheme or parsed_redirect.netloc:
		if parsed_request.netloc != parsed_redirect.netloc:
			return "/crm"
		redirect_url = parsed_redirect.path or "/crm"
		if parsed_redirect.query:
			redirect_url = f"{redirect_url}?{parsed_redirect.query}"

	if not redirect_url.startswith("/"):
		redirect_url = "/" + redirect_url

	is_safe = any(redirect_url.startswith(p) for p in SAFE_REDIRECT_PREFIXES)
	if not is_safe and redirect_url not in ("/", "/crm"):
		return "/crm"

	return redirect_url
