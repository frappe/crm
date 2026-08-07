"""
crm.api.route_guard
~~~~~~~~~~~~~~~~~~~~
Route guard that blocks non-allow-listed users from Frappe Desk.

Registered as a ``before_request`` hook in ``hooks.py``. Tiberbu CRM suppresses all
native Frappe surfaces — internal users live in the ``/crm`` SPA, not the desk.

Design (mechanism verified empirically on Frappe v16.17.4; mirrors the proven
careverse_hq implementation):
- Only an allow-listed user may reach Desk (``/app*``, ``/desk*``): ``Administrator``
  (hardcoded floor) plus any usernames in the ``desk_access_users`` site_config array.
  This is a *username* check, NOT a role check — a System Manager not on the list is
  still blocked. DENY-FIRST: not on the list => blocked.
- Any other authenticated user is redirected (303) to the branded ``/access-restricted``
  page (a ``www/`` page, not a SPA route — so the block works with or without a frontend).
- Guests pass through so Frappe's normal login flow is preserved.

Redirect mechanism: from a ``before_request`` hook, ``frappe.local.response["type"]``
and ``frappe.Redirect`` both FAIL for a web-page GET (the former is only read by the
JSON/API responder; the latter is an Exception caught only *inside* the page-render
pipeline, which runs after ``before_request``). The one mechanism that works is raising
werkzeug's ``RequestRedirect`` — Frappe core catches exactly this in
``website/path_resolver.py`` and ``frappe/app.py`` turns any pipeline ``HTTPException``
into ``e.get_response()``. ``code = 303`` makes the browser re-issue a GET to the block
page. ``RequestRedirect`` lives in werkzeug (a hard Frappe dependency across v14→v16), so
this is version-stable.

Portability: zero frontend coupling — only the ``hooks.py`` wiring differs per app.
Runs on every request but exits immediately for non-desk paths (a couple of string
comparisons, no DB or role lookup), so the overhead is negligible.
"""
import frappe
from werkzeug.routing import RequestRedirect

# The account that may ALWAYS reach Desk. Hardcoded floor by design: it can never be
# removed via config, so a bad/empty site_config can't lock everyone out. A username
# match (not a role) sidesteps role-name drift and the "Administrator is not surfaced as
# System Manager in get_roles()" gotcha.
DESK_ADMIN_USER = "Administrator"

# Finance Cockpit page path — allow through for Finance roles without full desk access
FINANCE_COCKPIT_PATH = "/app/finance-cockpit"
FINANCE_COCKPIT_ROLES = frozenset([
    "Finance Manager", "AR Accountant", "AP Accountant",
    "Sales Manager", "Partner RM", "System Manager",
])

# site_config.json key holding EXTRA usernames permitted to reach Desk, e.g.:
#   "desk_access_users": ["ops@example.com", "sre@example.com"]
# Lives in site_config (not a DocType) on purpose: the allowlist gates System Managers,
# so it must not be editable from the surface it gates.
DESK_ACCESS_USERS_KEY = "desk_access_users"

# Where blocked users land. Deliberately named so it shares NO prefix with /app or /desk
# — loop-safety is then structural (the desk-path test can never match this route).
UNAUTHORIZED_ROUTE = "/access-restricted"


def _desk_allowed_users() -> set:
	"""Resolve the set of usernames permitted to reach Desk.

	Always includes ``Administrator`` (hardcoded floor) plus any valid entries from the
	``desk_access_users`` site_config array. DENY-FIRST: a missing, empty, or malformed
	key degrades safely to Administrator-only — never fail-open.
	"""
	allowed = {DESK_ADMIN_USER}
	try:
		configured = frappe.conf.get(DESK_ACCESS_USERS_KEY)
		if isinstance(configured, (list, tuple)):
			allowed.update(u.strip() for u in configured if isinstance(u, str) and u.strip())
	except Exception:
		# Any failure resolving config -> Administrator-only (fail-safe, deny-first).
		pass
	return allowed


def is_desk_allowed(user: str | None) -> bool:
	"""Public predicate: may ``user`` reach Desk? (username check, server-authoritative)."""
	return bool(user) and user in _desk_allowed_users()


def _has_finance_cockpit_role(user: str) -> bool:
	try:
		return bool(FINANCE_COCKPIT_ROLES & set(frappe.get_roles(user)))
	except Exception:
		return False


def _is_desk_path(path: str) -> bool:
	"""True only for the desk app itself: ``/app``, ``/app/...``, ``/desk``, ``/desk/...``.

	Exact-or-slash anchoring (NOT a bare ``startswith``) avoids false positives on routes
	that merely share the prefix string (``/application``, ``/apps``). The block page
	(``/access-restricted``) shares NO prefix with ``/app``/``/desk``, so it can never be
	re-matched here — redirect-loop safety is structural.
	"""
	p = (path or "").rstrip("/")
	return p in ("/app", "/desk") or p.startswith("/app/") or p.startswith("/desk/")


def pin_home_page_to_landing():
	"""Force the site root ('/') to resolve to the branded landing ('index') on every
	request. Registered as a ``before_request`` hook AHEAD of ``guard_desk_access``.

	Why this is required (desk-fence airtightness): Frappe's ``get_home_page()`` resolves
	'/' to a System User's ``default_workspace`` -> ``/desk/<workspace>`` BEFORE
	``www/index.py`` ever runs. Without this pin, a non-allow-listed System User who has a
	default workspace and simply visits '/' is served the native desk shell at the root —
	and the guard never fires, because it keys on ``frappe.request.path`` which is '/'
	(not a ``/app``|``/desk`` path). ``get_home_page()`` returns
	``frappe.local.flags.home_page`` verbatim when set (verified: frappe website/utils.py),
	so pinning it here forces '/' -> index -> (logged-in) redirect to /crm, closing the
	bypass. Cheap and per-request (flags reset each request); only ``/`` resolution reads it.
	"""
	frappe.local.flags.home_page = "index"


def guard_desk_access():
	"""Block users not on the desk allow-list from Frappe Desk.

	- Guest users: allow through (Frappe handles redirect-to-login).
	- Allow-listed users (Administrator + ``desk_access_users``): allow through.
	- Any other authenticated user: 303 redirect to the branded unauthorized page.
	"""
	request_path = frappe.request.path if frappe.request else ""

	# Early exit: only act on desk routes. Everything else (/crm, /api, /login, static
	# assets, the block page itself) is untouched.
	if not _is_desk_path(request_path):
		return

	user = frappe.session.user

	# Let Frappe handle guest -> login redirect.
	if not user or user == "Guest":
		return

	# Permitted accounts: Administrator (always) + configured desk_access_users.
	if is_desk_allowed(user):
		return

	# Finance Cockpit: allow users with Finance roles to reach /app/finance-cockpit.
	# Use exact-or-slash anchoring (same discipline as _is_desk_path) to avoid
	# prefix false-positives from routes that merely start with the same string.
	p = (request_path or "").rstrip("/")
	if p == FINANCE_COCKPIT_PATH or p.startswith(FINANCE_COCKPIT_PATH + "/"):
		if _has_finance_cockpit_role(user):
			return

	# Non-allow-listed user attempting desk access -> branded unauthorized page.
	# Audit trail: log the blocked attempt (no secrets/PII beyond user + path).
	try:
		frappe.logger("desk_access_guard").info("Blocked desk access: user=%s path=%s", user, request_path)
	except Exception:
		# Logging must never break the guard.
		pass

	# Raise a werkzeug redirect (see module docstring): the only mechanism that actually
	# redirects a web-page GET from a before_request hook. 303 => browser re-fetches with GET.
	exc = RequestRedirect(UNAUTHORIZED_ROUTE)
	exc.code = 303
	raise exc
