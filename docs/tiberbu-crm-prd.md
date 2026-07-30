# Product Requirements Document — Tiberbu CRM

**Product:** Tiberbu CRM (customized fork of Frappe CRM)
**Companion to:** [tiberbu-crm-brd.md](./tiberbu-crm-brd.md) — read the BRD first for goals, use cases, and scope.
**Document status:** Draft v0.1 — for review
**Date:** 2026-07-29
**Author:** Salim

---

## 0. How to read this PRD

The BRD says *what* and *why*; this PRD says *how*, at the level an engineer can implement against. It is organized by the epics defined in BRD §15.1 (E1–E7). Every design decision is checked against three constraints from the BRD:

1. **Fork-safe** — additive files over core edits; `git merge upstream/develop` must stay clean (BRD §4).
2. **Context7-validated** — Frappe/frappe-ui claims verified against `/frappe/frappe`, `/frappe/crm`, `/frappe/frappe-ui`. Avaya *vendor* APIs are flagged as build-time discovery, not verified here (BRD §6.2.1, R1).
3. **Proven pattern reuse** — the sibling app `careverse_hq` already solved native-surface suppression + MFA-faithful login; we replicate it, re-skinned.

> **Stack (authoritative):** Frontend = Vue 3 + frappe-ui + Tailwind (SPA under `/crm`). Backend = Frappe v15 / Python, MariaDB. Auth/landing surfaces = plain Jinja `www/` pages (outside the Vue app). **Not React/antd.**

### Codebase anchors (verified this session)
| Concern | File · symbol |
|---|---|
| SPA router + auth guard | `frontend/src/router.js` — `createWebHistory('/crm')` (L154), `router.beforeEach` (L158), guest redirect `window.location.href = '/login?redirect-to=/crm'` (~L226) |
| SPA boot / server gate | `crm/www/crm.py` — `get_context()` throws `PermissionError` if `check_app_permission()` fails (L14–19), `no_cache = 1` (L11) |
| Theme tokens | frappe-ui Tailwind preset → semantic CSS vars (`--surface-*`, `--ink-*`, `--outline-*`); app override point `frontend/src/index.css`; `frontend/tailwind.config.js` (empty `theme.extend`) |
| Brand mark | `frontend/src/components/Icons/CRMLogo.vue` (`fill="#EF0BF5"`); runtime brand via `FCRM Settings` (`brand_name`/`brand_logo`/`favicon`) surfaced in `frontend/src/stores/settings.js` |
| Telephony platform | `crm/integrations/api.py` — `_get_recording_credentials()` (L11), `is_call_integration_enabled()` (L33), `set_default_calling_medium()` (L56), `get_recording_url()` (L165) |
| Call log model | `crm/fcrm/doctype/crm_call_log/crm_call_log.json` — `telephony_medium` options `"\nManual\nTwilio\nExotel"` (L152); controller `crm_call_log.py` `link_with_reference_doc()` (L135), `recording_url_path` in `as_dict` |
| Call UI router (frontend) | `frontend/src/components/Telephony/CallUI.vue` — `TwilioCallUI`/`ExotelCallUI` refs (L2–3), `setMakeCall` (L129); providers `ExotelCallUI.vue`, `TwilioCallUI.vue` |
| Provider settings shape | `crm/fcrm/doctype/crm_exotel_settings`, `crm_twilio_settings`, `crm_telephony_agent` (`default_medium` Select = Twilio/Exotel) |
| Reference implementation | `apps/careverse_hq/careverse_hq/www/{index,login,access_restricted}.*`, `careverse_hq/api/route_guard.py`, `careverse_hq/branding.py`, `hooks.py` (`home_page`, `website_route_rules`, `before_request`) |

---

## 1. System architecture overview

```
                         ┌─────────────────────────────────────────────┐
   Guest / Prospect ───► │  www/index (Jinja)  — public landing (E3)    │
                         │  www/login (Jinja)  — branded login (E2)     │──POST /api/method/login (stock)
                         │  www/access-restricted (Jinja) — 401 (E2)    │
                         └───────────────┬─────────────────────────────┘
                                         │ authenticated
                                         ▼
   home_page="index" ───────►  Vue 3 SPA under /crm  (re-skinned, E1)
   before_request guard ─┐            │
   (fences /app, E2)     │            ├── Leads / Deals / Contacts / …
                         │            ├── Telephony CallUI (E4/E5/E6)
                         ▼            └── Journeys surfacing (E7)
                Frappe desk /app
                (allow-list only)

   Backend (Frappe/Python):
     crm/integrations/{twilio,exotel,avaya}/  ← Avaya added (E4/E5/E6)
     crm/integrations/api.py  (provider-agnostic registry + recording proxy)
     CRM Call Log · CRM Telephony Agent · CRM {Twilio,Exotel,Avaya} Settings
     SLA + Assignment Rule + scheduler + CRM Notification  (E7)
```

**Three planes, three fork-safety strategies:**
- **Web/auth plane (E2, E3):** new `www/` pages + `hooks.py` keys + one `before_request` module. Pure addition; zero core edits.
- **Theme plane (E1):** CSS-variable overrides in `frontend/src/index.css` + logo edit + settings. No `node_modules`, no component rewrites.
- **Backend/telephony plane (E4–E7):** new `crm/integrations/avaya/` module + new doctypes; the only edits to *shared* files are two additive enum/branch lines (call-log `telephony_medium`, recording-credential resolver) — marked and minimal.

---

## 2. E1 — Tiberbu re-skin (red / black / white)

### 2.1 Design
frappe-ui exposes color as semantic CSS variables generated from its Tailwind preset (context7: `/frappe/frappe-ui` — `--surface-*`, `--ink-*`, `--outline-*`, dark mode via `[data-theme="dark"]`). Black/white is already the default (gray ramp + white surfaces). Re-skin = **re-hue the interactive tokens to Tiberbu red**, leave surfaces/ink neutral.

### 2.2 Implementation

**a) Token overrides** — append to `frontend/src/index.css` (which already imports `frappe-ui/style.css` first, so overrides win):

```css
:root {
  /* Primary action (solid Button reads these) — was gray/900 near-black */
  --surface-gray-10: #bc1823;  /* Tiberbu primary red */
  --surface-gray-9:  #a5141f;  /* hover */
  --surface-gray-8:  #8f111b;  /* active */
  /* Interactive/link/checkbox — retire default blue */
  --blue-500: #bc1823;
  --ink-blue-link: #bc1823;
}
[data-theme="dark"] {
  --surface-gray-10: #e5303c;  /* lighter red for contrast on dark */
  --surface-gray-9:  #cf2531;
  --surface-gray-8:  #b81d28;
  --blue-500: #e5303c;
}
```
> Exact steps/hex to be tuned in design review against WCAG AA (BRD B4/R4 — keep semantic error-red distinct from brand-red). The token *names* above are the correct override points; values are the design variable.

**b) Brand mark** — `frontend/src/components/Icons/CRMLogo.vue` L11 `fill="#EF0BF5"` → Tiberbu logo. Prefer replacing with the official Tiberbu SVG once provided.

**c) Runtime branding** — set `brand_name` = "Tiberbu CRM", `brand_logo`, `favicon` on **FCRM Settings** (already surfaced by `stores/settings.js`). Static fallbacks: `frontend/index.html` + `crm/www/crm.html` `<title>`, `frontend/vite.config.js` PWA manifest.

**d) Stray hardcoded hex sweep** (from frontend map): `ThemeSwitcher.vue` dots, `RatingInput.vue` stars, event-color defaults (`#30A66D`), `GeolocationControl.vue` (`#4f46e5`) — reviewed for brand consistency, semantic colors preserved.

### 2.3 Fork-safety
`index.css` and `CRMLogo.vue` are app files rarely touched upstream; conflicts (if any) are trivial. **No `tailwind.config.js` palette rewrite** (coarser, fights the `var()` layer) unless design requires a new `brand` scale.

### 2.4 Proof
Side-by-side screenshots, **light + dark**, across landing / list / detail / dialog / primary buttons. Grep `#[0-9a-fA-F]{3,8}` shows no off-brand accents survive.

---

## 3. E2 — Native-surface suppression, default route, MFA-faithful login

This is the highest-complexity epic; it mirrors `careverse_hq` mechanism-for-mechanism, re-skinned. **Split into 4 stories** (S2.1 routing/home, S2.2 access-restricted+guard, S2.3 branded login **incl. full MFA**, S2.4 graceful logout) because of auth-state surface area (BRD §5.3.1).

### 3.1 `hooks.py` additions (additive keys)
```python
home_page = "index"                      # site root → branded landing (context7: overrides Website Settings)
website_route_rules = [
    {"from_route": "/crm/<path:app_path>", "to_route": "crm"},        # existing
    {"from_route": "/crm-form/<route>", "to_route": "crm_form"},      # existing
    {"from_route": "/login", "to_route": "login"},                    # NEW → branded login shadow
]
before_request = ["crm.api.route_guard.guard_desk_access"]           # NEW → desk fence
```
> **Precedence caution (verify at build):** confirm `home_page="index"` does not regress the existing `/crm` app routing or Frappe's `default_workspace`-on-login behavior (context7: `website/utils.py _get_home_page` redirects to a user's `default_workspace` if set). CRM users should have no desk `default_workspace`, so root → landing → (logged in) SPA. Test both guest and logged-in root hits.

### 3.2 Web pages (new `www/` shadows)
| File | Role | Key `get_context` behavior |
|---|---|---|
| `crm/www/index.py` + `index.html` | Public landing (E3 owns content) | `no_cache=True`; if `session.user != "Guest"` → `frappe.local.flags.redirect_location='/crm'; raise frappe.Redirect`; `no_header`/`no_breadcrumbs`; brand context |
| `crm/www/login.py` + `login.html` | Branded login (S2.3) | `no_cache=True`; redirect-if-logged-in; sanitize `redirect-to`; expose `provider_logins`, `ldap_settings`, `disable_signup`/`disable_user_pass_login`/`login_with_email_link`, login label; `context.redirect_to` default `/crm` |
| `crm/www/access-restricted.html` + `access_restricted.py` | Branded 401 (S2.2) | `no_cache=True`; defense-in-depth: Administrator→`/app`, Guest→`/login`, else render; `<meta robots noindex>` |

> **context7 note:** `allow_guest` is **not** a recognized module-level property for www controllers; guest access is the default for `www/` pages and any gating happens inside `get_context()`. `no_cache` **is** recognized. (Validated against `/frappe/frappe` `template_page.py`.)

### 3.3 Desk fence — `crm/api/route_guard.py` (copied from careverse_hq, renamespaced)
- `guard_desk_access()` runs on every request; early-exits unless path is slash-anchored `/app` or `/desk`.
- Guests pass (Frappe handles guest→login). Allow-list = `Administrator` + `site_config.json["desk_access_users"]` (username check, deny-by-default — **not** role-based).
- Blocked → `raise RequestRedirect("/access-restricted")` with `.code = 303` (from `werkzeug.routing`). **This is the only redirect that works from `before_request`** — `frappe.Redirect` is caught later in the render pipeline; careverse_hq documents testing this. `/access-restricted` shares no prefix with `/app`/`/desk` → no loop.
- **Fork-safety + risk (BRD R7):** admin lockout guarded by Administrator floor + documented `desk_access_users`. Add a bench-command/README note for adding technical users.

### 3.4 S2.3 — Branded login with FULL Frappe auth parity (BRD §5.3.1, hard gate)

**Server (`login.py`)** mirrors Frappe's login context so the template can honor system settings (see 3.2). Reuse careverse_hq's `sanitize_redirect` (block external netloc; force internal `/`-prefix; allow-list `['/crm','/app','/api','/desk']`; default others to `/crm`).

**Client (`login.html`, vanilla JS — no frappe.ui/login.js)** implements the full state machine against **stock `/api/method/login`** (context7-validated contract, `/frappe/frappe` `auth.py`+`twofactor.py`):

```
POST /api/method/login {usr, pwd}   (credentials: same-origin, X-Frappe-CSRF-Token)
  → message "Logged In"     → redirect to sanitized redirect_to (default /crm)
  → message "No App"        → treat as success → /crm
  → message "Password Reset"→ follow data.redirect_to (expired pwd) — NOT an error
  → data.verification + data.tmp_id (message ≠ "Logged In")  → MFA STEP:
        persist tmp_id (cookie + memory)
        render prompt from verification{method, prompt, setup, token_delivery}
        POST /api/method/login {otp, tmp_id}  → confirm_otp_token → "Logged In"
```

**MFA methods** (driven by System Settings `two_factor_method`) — all three required:
- **OTP App** (TOTP): if `setup === false` (first login), guide through QR/email provisioning (`/qrcode`), else prompt for authenticator code.
- **SMS** / **Email**: if `token_delivery === false`, show "code not sent, contact admin" rather than a dead input.

**Also handle:** wrong code + expired `tmp_id` ("Login session expired…") → clear `tmp_id`, allow retry/restart; social buttons from `provider_logins` (suppress during OIDC authorize flow); LDAP when enabled; the `disable_*`/label gates. Seed `window.csrf_token` via Jinja.

**Do NOT** override the `login`/`logout` whitelisted methods in `hooks.py` — only shadow the *page*. This preserves upstream auth behavior and keeps the fork clean.

### 3.5 S2.4 — Graceful logout
SPA + pages point at **stock `/api/method/logout`**, then navigate to branded `/login?redirect-to=<current>`. The "Log out" item in `AppSidebar`/`UserDropdown` uses this. No hook, no method override. Because `/` (index) and `/login` are both shadowed, the user never lands on a stock Frappe page post-logout.

### 3.6 Branding helper
Port a small `crm/branding.py` (`get_configured_app_brand()` + `apply_brand_context(context, brand, surface=...)`) reading **FCRM Settings** (reuse existing `brand_name`/`brand_logo`/`favicon`) so all three Jinja pages share one brand source. Assets under `crm/public/images/`. No global website theme / `app_include_css` (matches careverse_hq — per-page branding only).

### 3.7 Proof (hard gate)
1. 2FA **OTP App** user: password → code → CRM (recording). 2. Same for **SMS** and **Email**. 3. First-time OTP enrollment completes. 4. Password-expired → reset (not error). 5. Wrong/expired OTP → recoverable, no lockout, no stock screen. 6. Social (if configured) + LDAP (if enabled). 7. Parity: branded page and stock `/login` reach same authed state for a 2FA user. 8. Clean-session walkthrough root→login→app→access-restricted→logout with **zero** stock Frappe screens; `/app` blocked for non-allow-listed, allowed for allow-listed.

---

## 4. E3 — Landing page (public)

### 4.1 Design
`crm/www/index.{py,html}` — plain Jinja (no bundle mount), structurally modeled on `careverse_hq/www/index.html` but re-skinned to Tiberbu red/black/white and CRM typography. Redirect-if-logged-in → `/crm` (see 3.2).

### 4.2 Content (BRD A3/A4)
- Hero: Tiberbu wordmark, tagline "Powering Better Health", H1 value prop for Careverse CRM, primary CTA **Get Started/Sign In** → `/login`, secondary CTA **Request a demo**.
- **Demo CTA → real Lead:** posts to the existing public lead-capture form engine (`crm/www/crm_form.py` / `crm/api/form.py`) so a submission becomes a **CRM Lead** (BRD UC-S1). Reuse, don't rebuild. Assignment via existing Assignment Rules.
- Feature cards (Careverse customer-journey messaging), footer.

### 4.3 Fork-safety & proof
New files only. Proof: logged-out screenshot (branded, no stock chrome) + a Lead created from the demo CTA appears in the CRM list; logged-in visitor at `/` bounces to SPA.

---

## 5. E4 — Telephony platform + Avaya forms (no credentials needed)

**Goal (BRD §6.2.2):** ship every Avaya config form so the credential handoff is turnkey. E4 is dependency-free.

### 5.1 New DocType — `CRM Avaya Settings` (Single)
Modeled on `crm_exotel_settings`. Fields (indicative; finalize per live edition, R1):

| Field | Type | Notes |
|---|---|---|
| `enabled` | Check | Lists Avaya alongside Twilio/Exotel in the platform |
| `mode` | Select | `Cloud (AXP)` / `On-Prem (Aura/AES)` — gates fields via `depends_on` |
| `record_calls` | Check | |
| `webhook_verify_token` | Data | Guards inbound webhook (Exotel precedent) |
| **Cloud (AXP)** | | `axp_base_url`, `axp_region`, `client_id`, `client_secret` (**Password**), `account_id` |
| **On-Prem (AES)** | | `aes_host`, `cti_user`, `cti_password` (**Password**), `dmcc_or_tsapi_link`, `cm_id`, `recorder_base_url`, `recorder_auth` (**Password**), `connector_endpoint` |

All secrets use `Password` fieldtype (encrypted at rest) — matches Twilio/Exotel.

### 5.2 Extend existing (minimal, marked edits)
- **`crm_call_log.json` L152:** `"\nManual\nTwilio\nExotel"` → `"\nManual\nTwilio\nExotel\nAvaya"`. (One-line additive enum; also update the `CRMCallLog` type Literal in `crm_call_log.py`.)
- **`crm_telephony_agent`:** add `avaya_number` (Data, mirrors `exotel_number`); add `Avaya` to `default_medium` Select.
- **`crm/integrations/api.py`:**
  - `_get_recording_credentials()` (L11): add `elif telephony_medium == "Avaya":` branch returning per-mode recording auth.
  - `is_call_integration_enabled()` (L33): include Avaya in the returned integrations map so the frontend offers the Avaya call UI.

### 5.3 Frontend registration
- New `frontend/src/components/Telephony/AvayaCallUI.vue` (mirrors `ExotelCallUI.vue` — closest template for a server-side/webhook provider).
- Register in `CallUI.vue`: add `<AvayaCallUI ref="avaya" />`, an `avaya` ref, and an entry in the provider list (L67-68 pattern), routing `makeOutgoingCall` when medium = Avaya.
- New settings screen under `frontend/src/components/Settings/Telephony/` for CRM Avaya Settings.

### 5.4 Proof
Screenshot of CRM Avaya Settings showing **both** mode field sets with `mode` toggling; `Avaya` selectable as `default_medium` on Telephony Agent and as a medium on Call Log — **with no credentials entered**; UI clearly indicates "not connected".

---

## 6. E5 / E6 — Avaya connect (gated on Tiberbu credentials, R1)

Both modes converge on the shared `CRM Call Log` shape, the same realtime screen-pop event, and the same recording proxy (`get_recording_url`, `recording_url_path`). Only the connector behind `mode` differs.

### 6.1 E5 — Cloud (AXP) — do first (closest to Exotel)
New `crm/integrations/avaya/handler.py` modeled on `exotel/handler.py`:
- `@frappe.whitelist(allow_guest=True) handle_request(**kwargs)` — inbound/status webhook; `validate_request()` via `webhook_verify_token`; `frappe.publish_realtime("avaya_call", payload)` (frontend `AvayaCallUI` socket listener); create/update `CRM Call Log`; resolve caller via `get_contact_by_phone_number` (screen-pop, BRD UC-B1); `link_with_reference_doc`.
- `@frappe.whitelist() make_a_call(to_number, ...)` — AXP REST outbound; store `recording_url`.
- Recording playback flows through existing authenticated `get_recording_url` proxy (never public — BRD R2).

> Exact AXP REST/webhook payloads = build-time discovery against Tiberbu's tenant (R1). The Frappe wiring above is validated (`/frappe/crm` `exotel/handler.py`).

### 6.2 E6 — On-Prem (Aura/AES)
Same `handler.py`, `mode == "On-Prem"` branch. AES CTI (TSAPI/DMCC) typically needs a **server-side connector/bridge** inside Tiberbu's network translating CTI events → the same webhook/realtime path; recordings from the on-prem recorder URL stored in `recording_url`. Connector topology decided in discovery.

### 6.3 Compliance gate (BRD R2)
Before recording go-live: consent, retention, Kenya DPA 2019 data-residency confirmed. Recordings stay authenticated/proxied.

### 6.4 Proof
E5: inbound screen-pop + outbound call, both logged with playable recording. E6: call logged via AES path with recording.

---

## 7. E7 — Support-journey automation

### 7.1 Design — compose existing primitives (no new engine)
Frappe CRM already has the building blocks (BRD §6.1, backend map):
- **SLA** — `CRM Service Level Agreement` (`apply()`, working hours via `crm_service_day`/holiday list); auto-applied on Lead/Deal `before_validate`/`before_save`; progressed by `Communication` doc_events.
- **Assignment** — core `Assignment Rule` (round-robin/territory) + `assign_agent()`.
- **Scheduler** — `hooks.py scheduler_events` (cron/hourly/daily) for time-based steps.
- **Notifications** — `CRM Notification` + `publish_realtime`.

### 7.2 Journeys to deliver
- **Onboarding (UC-B3):** won Deal → staged tasks + owner assignment + SLA-timed reminders until facility live. Trigger via a **new `CRM Deal` doc_event** in `hooks.py` (additive) + scheduler follow-ups. (Avoid `on_update` side-effects per team rules — use an explicit handler.)
- **Missed-call recovery (UC-B4):** missed inbound Avaya call → callback Task with SLA timer + on-duty notification. Hangs off the call-log status set by the Avaya handler.

### 7.3 Data
A light `CRM Journey` / `CRM Journey Step` definition doctype **only if** config-driven journeys are needed beyond what Assignment Rules + SLA express; otherwise implement as scheduled handlers. Decide in E7 design spike.

### 7.4 Proof
On a test account: SLA timer starts, auto-assignment fires, escalation/reminder triggers — shown via doc state + notification.

---

## 8. Data model summary (deltas only)

| DocType | Change | Type |
|---|---|---|
| `CRM Avaya Settings` | **New** Single (dual-mode fields, §5.1) | Additive |
| `CRM Telephony Agent` | + `avaya_number`; `default_medium` += `Avaya` | Additive field/enum |
| `CRM Call Log` | `telephony_medium` += `Avaya` (L152) | 1-line enum |
| `CRM Deal` | new doc_event handler (onboarding journey) | Additive hook |
| `CRM Journey` / `Step` | **New** (only if config-driven journeys needed) | Additive, conditional |
| `FCRM Settings` | reuse `brand_name`/`brand_logo`/`favicon` | No change |

No modifications to Lead/Deal/Contact schemas beyond the above. No destructive migrations.

---

## 9. API contract deltas

| Method | Change | Auth |
|---|---|---|
| `crm.integrations.api.is_call_integration_enabled` | include Avaya in map | session |
| `crm.integrations.api._get_recording_credentials` | + Avaya branch | internal |
| `crm.integrations.avaya.handler.handle_request` | **new** webhook | `allow_guest=True` + token |
| `crm.integrations.avaya.handler.make_a_call` | **new** outbound | session |
| Realtime event `avaya_call` | **new** publish/subscribe | socket (user-scoped) |
| `/api/method/login`, `/api/method/logout` | **unchanged** (page-shadow only) | stock |

All new whitelisted methods carry **type annotations** (`hooks.py` sets `require_type_annotated_api_methods = True`).

---

## 10. Fork-maintainability plan (BRD §4)

| Plane | Files | Merge risk |
|---|---|---|
| Web/auth | `www/{index,login,access_restricted}.*`, `api/route_guard.py`, `branding.py` (new) | ~none (new files) |
| hooks.py | `home_page`, `+1 website_route_rule`, `before_request` (new keys) | low (distinct keys; 3-way clean) |
| Theme | `index.css` (append), `CRMLogo.vue` | trivial |
| Telephony | `integrations/avaya/*` (new), `AvayaCallUI.vue` (new) | ~none |
| Shared edits (marked) | `crm_call_log` enum, `_get_recording_credentials`, `is_call_integration_enabled`, `crm_telephony_agent`, `CallUI.vue` provider list | low — small, semantically obvious diffs |

**Merge protocol:** after each `git fetch upstream` → `git merge upstream/develop`, run the E2 walkthrough + telephony smoke test. Keep shared-file edits to the marked lines so conflicts (if any) are one-liners. Never edit `node_modules`/`frappe-ui` submodule.

---

## 11. Cross-cutting NFRs

- **Security:** login open-redirect sanitized; webhook token-guarded; recordings authenticated-proxy only; desk deny-by-default; guest reaches only landing + `/login`.
- **Dark/light parity:** every E1/E3 surface verified both themes (auth pages fixed-light per careverse_hq convention is acceptable; app is theme-aware).
- **i18n:** use `_()` in Jinja pages; frappe-ui translation plugin in SPA.
- **Perf:** `no_cache` on auth pages (correct, not a regression); landing static-ish.
- **Accessibility:** brand red vs. semantic error-red kept distinguishable (WCAG AA, BRD B4).

---

## 12. Delivery sequence & dependencies

```
E1 (re-skin) ─┐
E2 (auth/native surface, incl. MFA) ─┼─ no external dep → start now
E3 (landing) ─┤     (E3 visually depends on E1 tokens)
E4 (Avaya forms) ─┘
                 └─► E5 (Avaya Cloud connect) ─► E6 (Avaya On-Prem)   [gated: Tiberbu creds, R1]
E7 (journeys) ── after E4/E5 (missed-call journey needs call events); onboarding journey can start earlier
```

**BMAD posture (BRD §15):** each story → its own vertical slice + proof; stops at `review`; mandatory second-pass review (data-shape, dead code, null/falsy-zero, API contract, dark/light); agents never set `done`. Context7 re-checked at build against the *installed* Frappe version (2FA internals especially).

---

## 13. Open build-time discovery (not blockers to start E1–E4)

1. **Avaya (R1):** live edition(s), AXP tenant REST/webhook contracts, AES CTI access + recorder auth, connector topology for on-prem.
2. **Brand assets:** official Tiberbu logo SVG; canonical hex confirmation + any secondary colors.
3. **`home_page` precedence:** confirm no regression to `/crm` routing or `default_workspace`-on-login for any existing user profile.
4. **Compliance (R2):** recording consent, retention, Kenya DPA residency.
5. **Landing copy owner** (BRD A4).

---

*This PRD is at `review`. On sign-off, decompose E1–E7 into stories in the tracker and begin E1–E4 (dependency-free). E5/E6 start on the Avaya credential handoff; E4 ensures that handoff is configuration-only.*
