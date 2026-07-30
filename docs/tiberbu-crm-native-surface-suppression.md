# E2 — Native-Surface Suppression + Branded Auth

**Epic:** E2 · **Stories:** S1 routing, S2 desk fence + branded 401, S3 branded login (MFA parity), S4 graceful logout + branding helper.
**Status:** review · **Date:** 2026-07-30 · **Site:** `cr-dev.tiberbu.app`

Reference implementation: `apps/careverse_hq` (proven native-surface replacement), re-skinned to Tiberbu red `#bc1823`.

---

## Files (all additive except two minimal, marked core edits)

| File | Kind | Purpose |
|---|---|---|
| `crm/branding.py` | new | Reads FCRM Settings → brand dict; `apply_brand_context()` for all www pages |
| `crm/api/route_guard.py` | new | `before_request` desk fence; raises `werkzeug RequestRedirect(303)` |
| `crm/www/login.py` + `login.html` | new | Branded login **page** (shadows stock `/login`); POSTs to stock `/api/method/login`; full MFA client JS |
| `crm/www/index.py` + `index.html` | new | Public landing at site root (`home_page = "index"`) |
| `crm/www/access_restricted.py` + `access-restricted.html` | new | Branded 401; JS "Sign out" POSTs logout w/ CSRF |
| `crm/public/images/tiberbu-mark.svg` | new | Static red brand mark for www pages |
| `crm/hooks.py` | **core edit (marked)** | `home_page="index"`, `before_request` guard, `/login` route rule |
| `crm/www/crm.py` | **core edit (marked)** | guest branch → branded login instead of 403 throw |

The two core edits are the minimum needed to route requests into the additive pages; both are commented with `E2-S…` markers for merge visibility.

## E2-S1 — Routing

- `home_page = "index"` — site root serves the branded landing. context7-verified: `home_page` hook beats Website Settings (`website/utils.py get_home_page`), but a user's `default_workspace` overrides it. **Regression avoided** because `index.py` redirects any logged-in user to `/crm` before workspace resolution matters (a logged-in System User never lingers on `/` to be sent to a workspace).
- `website_route_rules` gains `{"/login" → "login"}` (existing `/crm/<path>` and `/crm-form/<route>` preserved).
- `before_request = ["crm.api.route_guard.guard_desk_access"]`.

## E2-S2 — Desk fence + branded 401

`guard_desk_access()` runs on every request, early-exits unless the path is slash-anchored `/app`|`/desk`. Guests pass (Frappe's own login redirect). Allow-list = `Administrator` (hardcoded floor) + `site_config.json["desk_access_users"]` (username check, deny-by-default). Blocked users → `RequestRedirect("/access-restricted", code=303)` — the only redirect that works from `before_request` (verified: `frappe.Redirect` is caught too late; `response["type"]` is ignored on the website path). `/access-restricted` shares no `/app`|`/desk` prefix → structural loop-safety.

## E2-S3 — Branded login with FULL MFA parity (BRD §5.3.1 HARD GATE)

`login.py` mirrors stock server context: `disable_signup`, `disable_user_pass_login`, `login_with_email_link`, composed `login_label`, `provider_logins` (`get_oauth2_providers()`, suppressed in OIDC authorize flow), `ldap_settings`, and `sanitize_redirect` (open-redirect guard, whitelist `/crm /app /desk /api`, default `/crm`). CSRF token passed to the page so the guest POST is accepted.

`login.html` client JS (vanilla, **not** frappe.ui) POSTs to the **unmodified** `/api/method/login` and handles every state (context7-validated against `/frappe/frappe` v16 `auth.py`+`twofactor.py`):
- `"Logged In"` (System User) / `"No App"` (Website User) / `"Password Reset"` → success (Password Reset follows `redirect_to`, else `/update-password`).
- `verification` + `tmp_id` → MFA step: persists `tmp_id` (cookie + memory), renders prompt from `verification{method,prompt,setup,token_delivery}`, re-POSTs `{otp, tmp_id}`.
- All 3 methods: **OTP App** (incl. first-time `setup===false` → block entry, show QR-email instructions), **SMS**, **Email** (proceed only when `token_delivery !== false`).
- Wrong/expired OTP recovery (surfaces server message, stays on step); "Use a different account" resets to credentials; social buttons; error scrubbing (no traceback/SQL leak).

We do **NOT** override the `login`/`logout` whitelisted methods — only shadow the page.

## E2-S4 — Graceful logout + branding helper

- `crm/branding.py` reads FCRM Settings (E1-S3 values) with module-default fallbacks; used by all www pages via `apply_brand_context`.
- SPA logout (`stores/session.js`) already POSTs stock `logout` then → `/login?redirect-to=/crm` (now our branded page).
- `crm.py` guest branch → `/login?redirect-to=/crm` (no stock 403).
- Access-restricted "Sign out": **finding & fix** — `/api/method/logout` is **POST-only** (verified: GET 403s, session survives; the careverse reference's GET anchor is actually broken here). Reworked to a CSRF-authenticated `fetch` POST → land on branded `/login`, fallback to stock `/logout` on error.

## Proof (all via Playwright on cr-dev, Host-header routed)

| Check | Result | Artifact |
|---|---|---|
| Guest `/` → branded landing | 200, "Powering Better Health", no stock chrome | `e2-01-landing.png` |
| Guest `/login` → branded login | 200, "Welcome back", POSTs `/api/method/login` | `e2-02-login.png` |
| Sales User logs in via form | → `/crm/leads/view/list` | `e2-03-after-login.png` |
| Sales User (non-allow-listed) hits `/app` | → branded `/access-restricted` | `e2-04-access-restricted.png` |
| Admin (allow-listed) hits `/app` | → desk (allowed) | walkthrough log |
| **2FA OTP App**: password → MFA step | correct prompt, code field enabled | `e2-05-mfa-prompt.png` |
| **2FA OTP App**: live TOTP → success | → `/crm/leads/view/list` | `e2-06-mfa-success.png` |
| Wrong OTP | stays on step, "Incorrect Verification code" | `e2-07-wrong-otp.png` |
| "Use a different account" | resets to credentials, OTP disabled | recovery log |
| Guest `/crm` (SPA shell) | → branded `/login?redirect-to=/crm` (no 403) | curl 301 |
| Branded "Sign out" | session ends (`logged user = (none)`) → branded `/login` | `e2-11-signout-landing.png` |
| Assets `/assets/crm/images/tiberbu-mark.svg` | 200 image/svg+xml | curl |

Screenshots in `/tmp/crm-proof/e2-*.png`.

## Second-pass review fixes (applied)

- **BLOCKER — desk-fence bypass via site root**: a non-allow-listed System User with a
  `default_workspace` hitting `/` had the root resolve to `/desk/<workspace>` *before*
  `index.py` ran (the guard keys on `request.path == "/"`, so it never fired). **Fixed**
  by adding a `pin_home_page_to_landing` `before_request` hook (ahead of the guard) that
  sets `frappe.local.flags.home_page = "index"` — `get_home_page()` returns that verbatim,
  forcing `/` → index → `/crm` redirect. **Verified:** workspace-having System User at `/`
  now lands in `/crm` (`BYPASS? false`); `/app` still fences to `/access-restricted`.
- **BLOCKER — forced-password-reset stripped the reset key**: the client + server redirect
  whitelists lacked `/update-password`, so a reset `redirect_to`
  (`…/update-password?key=…`) was dropped and the user stranded. **Fixed** by adding
  `/update-password` to both `SAFE_REDIRECT_PREFIXES` (login.py) and the client
  `getSafeRedirectTarget` whitelist. **Verified:** the key survives; cross-origin and
  protocol-relative targets still coerce to `""`.
- **Website User "No App"** (nit): `crm.py` now redirects an authenticated-but-no-CRM-access
  user to `/access-restricted` instead of throwing the stock `PermissionError` page.
- **Dead context/DB read** (nit): removed the unused `disable_signup`,
  `login_with_email_link`, `is_oidc_login_flow`, `social_login` context vars and the
  per-request LDAP `get_value` (the template consumed none of them).

## Environment notes / watch-outs

- **Email 2FA method**: on cr-dev, Email OTP can't complete — no default outgoing Email Account **and** a stale `careverse_hq/templates/emails/otp_verification.html` override throws `TemplateNotFound`. Stock Frappe login fails identically here. Our page degrades gracefully (clean message, no traceback leak). OTP App (fully testable) proved the complete MFA flow. Re-verify Email/SMS once a mail account + SMS gateway exist.
- **Test fixture**: `sales.tester@tiberbu.test` (Sales User, pw `Tiberbu@Sales1`) created on cr-dev for the desk-fence + MFA proofs; 2FA toggled on then **restored to disabled** (original state). Remove the test user before any prod cut.
- **`desk_access_users`** not set in `site_config.json` → only `Administrator` reaches the desk. Add ops/SRE usernames there as needed.
- Upstream-merge: re-run this walkthrough after any `git merge upstream/develop`; watch the two core edits (`hooks.py`, `crm.py`) for conflicts.
