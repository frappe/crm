# Tiberbu CRM — Session Handoff

**Purpose:** resume the Tiberbu CRM customization in a fresh chat. Read this top-to-bottom before touching code.
**Date of handoff:** 2026-07-29 · **Branch:** `develop` · **Repo:** `/home/ubuntu/frappe-bench/apps/crm`

---

## 0. What this project is (one paragraph)

Tiberbu CRM is a **brownfield fork of `frappe/crm`** (upstream remote = `tiberbu/crm`, itself forked from `frappe/crm`; `frappe-ui` is a git submodule). It becomes the sales + customer-support layer around Tiberbu's **Careverse HMIS**, re-skinned to Tiberbu brand (**red `#bc1823` / black / white**), with a public landing page, suppression of all native Frappe surfaces, and an **Avaya** telephony integration (dual-mode: on-prem Aura/AES + cloud AXP). **Hard constraint: stay mergeable with upstream — additive files over core edits.**

**Stack (important — NOT React/antd):** Frontend = **Vue 3 + frappe-ui + Tailwind** SPA served at `/crm`. Backend = Frappe v15/v16 Python, MariaDB. Auth/landing surfaces = plain Jinja `www/` pages.

---

## 1. Read these first (already written, in `docs/`)

| Doc | What it is |
|---|---|
| `docs/tiberbu-crm-brd.md` | Business Requirements — goals, personas, use cases (Sales/Business/Technical), Req A (landing), Req B (re-skin), **Req C (no native surfaces + MFA parity §5.3.1)**, Avaya §6.2, epics E1–E7 |
| `docs/tiberbu-crm-prd.md` | Internal PRD — architecture, per-epic design, **verified codebase anchors (file:line)**, data-model & API deltas, fork-safety plan |
| `docs/avaya-integration-prd.md` | External doc for Avaya Eng — dual-mode, mechanism-per-interaction (webhook/REST/WebSocket), API payload examples, discovery questionnaire |
| `docs/tiberbu-crm-backlog.md` | **The story backlog — Sprints 1–5, E1–E7, each with a proof. This is your task list.** |

**Rules that govern this work** (from user's global `~/.claude/rules/`): context7 MANDATORY before any library-API claim (frappe/frappe-ui validated already); never create branches; never commit/push without explicit go-ahead; never `git add -A`; `bench restart` after Python changes; **BMAD posture — stories stop at `review`, agents never set `done`, proof-of-work required (UI = screenshot light+dark; backend = request/response); mandatory second-pass review.**

---

## 2. What's DONE and PROVEN (E1 partial)

**E1-S1 — brand token override** — `frontend/src/index.css` (lines after the `@import`): remapped the frappe-ui **blue interactive-accent token family** (`--surface-blue-*`, `--ink-blue-*`, `--outline-blue-*`, `--ink-blue-link`, raw `--blue-*` / `--dark-blue-*`) → Tiberbu red, in BOTH `:root` and `[data-theme="dark"]`. **Key insight:** black/white is already the frappe-ui default (gray ramp + white surfaces); the primary button is already near-black `#171717`. The only OFF-brand thing was the blue accent + magenta logo. So the re-skin = re-hue blue→red, DON'T touch neutral `--surface-gray-*` (those back tooltips/switches/badges too — verified blast radius).

**E1-S2 — logo + identity** — `CRMLogo.vue` fill `#EF0BF5`→`#BC1823`; `frontend/index.html` title→"Tiberbu CRM"; `frontend/vite.config.js` PWA manifest name/desc→Tiberbu.

**Verified working** (not just build-green): installed CRM on cr-dev, served, Playwright screenshots + pixel analysis confirmed light mode = red accent on white/black (blue gone), **dark mode renders (`#171717` base) with red carried through** — dark/light parity holds. Screenshots in `/tmp/crm-proof/*.png`.

**CRITICAL FORK FIX (already applied):** `crm/fcrm/doctype/crm_lead/crm_lead.py:8` and `crm/fcrm/doctype/crm_deal/crm_deal.py:6` imported the **private** `frappe.desk.form.assign_to._add`, which does NOT exist in Frappe v16.17.4 → CRM would not install. Changed to public `add as assign` (behavior-equivalent; CRM already passes `ignore_permissions=True`). **This is a required compat shim; keep it. Flag any other `frappe.*` private-symbol imports on future upstream syncs.**

---

## 3. Environment state (what I changed — all reversible, nothing committed)

- **cr-dev.tiberbu.app**: uninstalled `client_registry` (backup first: `sites/cr-dev.tiberbu.app/private/backups/20260729_224447-*`). Now has `frappe` + `erpnext` + **`crm` (installed)**.
- Admin password on cr-dev set (dev only) — stored in `.dev-credentials` (gitignored).
- A dev server may be running: `bench --site cr-dev.tiberbu.app serve --port 8005` (log `/tmp/crm-serve.log`). Re-start if gone.
- **Nothing is committed or pushed.** `git status` will show modifications to `index.css`, `CRMLogo.vue`, `index.html`, `vite.config.js`, `crm_lead.py`, `crm_deal.py`, plus new `docs/*.md`.

**Uncommitted git state note:** the repo also had pre-existing modifications when this work started (see original `git status`). Do NOT `git add -A`. Stage by name if/when the user authorizes a commit.

---

## 4. How to get browser proof (reuse this — it works)

CRM login page/API needs the right Host header. Playwright is at `apps/crm/node_modules/playwright-core` (CommonJS — `import pkg from ...; const {chromium}=pkg`). Chromium build 1234 is missing; use installed build:
`executablePath: '/home/ubuntu/.cache/ms-playwright/chromium_headless_shell-1228/chrome-headless-shell-linux64/chrome-headless-shell'`, `args:['--no-sandbox']`.
Route every request adding `host: 'cr-dev.tiberbu.app'`. Login via `POST /api/method/login` `{usr:'Administrator', pwd:'<see .dev-credentials>'}`. Toggle dark via `localStorage.setItem('theme','dark')` + `document.documentElement.setAttribute('data-theme','dark')` then reload. Working script: `/tmp/crm-proof/shot.mjs`. If the image-Read hook times out, verify objectively with PIL pixel analysis (count Tiberbu-red `#bc1823`±50 vs blue px) — that pattern is proven.

---

## 5. NEXT STEPS — ordered story plan

Sprints 1 (brand + Avaya forms) and 2 (auth/native-surface) have **no external dependency** and can run in parallel. Recommended order below. **Finish E1 first (quick), then E2 (highest value + complexity), then E3, E4, then gated E5/E6, then E7.**

### Immediate: finish E1
- **E1-S3 — runtime brand.** Set `FCRM Settings` (Single doctype) `brand_name`="Tiberbu CRM", `brand_logo`, `favicon` (surfaced by `frontend/src/stores/settings.js`). Document it. Proof: sidebar/header screenshot.
- **E1-S4 — hardcoded-hex sweep.** `grep -rE '#[0-9a-fA-F]{3,8}' frontend/src`. Re-hue off-brand accents (ThemeSwitcher dots, RatingInput stars, event-color default `#30A66D`, GeolocationControl `#4f46e5`) for brand consistency. **Preserve semantic status colors** (success green / error red / warning) — keep error-red distinct from brand-red (WCAG AA). Proof: grep report + screenshots.

### E2 — Native-surface suppression + branded auth (Sprint 2, no external dep, HIGHEST complexity)
**Reference implementation exists in this bench: `apps/careverse_hq`** — it already replaced all native Frappe surfaces. Replicate its mechanism, re-skinned. Study: `careverse_hq/www/{index,login,access_restricted}.*`, `careverse_hq/api/route_guard.py`, `careverse_hq/branding.py`, `careverse_hq/hooks.py`.

- **E2-S1 — routing.** In `crm/hooks.py` add: `home_page = "index"`; add `{"from_route":"/login","to_route":"login"}` to `website_route_rules` (keep existing `/crm/<path>` + `/crm-form`); `before_request = ["crm.api.route_guard.guard_desk_access"]`. **VERIFY (context7 says `home_page` overrides Website Settings, and Frappe redirects to a user's `default_workspace` on login — `website/utils.py _get_home_page`): confirm no regression to `/crm` routing or logged-in-root behavior for existing users.** Guest `/` → landing; logged-in `/` → SPA.
- **E2-S2 — desk fence + branded 401.** Copy `route_guard.py` (renamespace to `crm.api.route_guard`). Mechanism: `guard_desk_access()` on every request, early-exit unless slash-anchored `/app`|`/desk`; guests pass; allow-list = `Administrator` + `site_config.json["desk_access_users"]` (username check, deny-by-default); blocked → `raise werkzeug.routing.RequestRedirect("/access-restricted")` with `.code=303` (**the ONLY redirect that works from `before_request` — `frappe.Redirect` is caught too late; careverse_hq documents this**). Create `crm/www/access-restricted.{py,html}` (`no_cache=True`, `noindex`, branded, "Go to CRM"/"Sign out"→`/api/method/logout`). `/access-restricted` must NOT share `/app`|`/desk` prefix (loop-safety). Proof: non-allow-listed→`/app`→branded 401; allow-listed→desk.
- **E2-S3 — branded login w/ FULL MFA parity (BRD §5.3.1 — HARD GATE).** Create `crm/www/login.{py,html}` shadowing stock login. Server context mirrors Frappe (`disable_signup`, `disable_user_pass_login`, `login_with_email_link`, login label, `provider_logins`=`get_oauth2_providers()`, `ldap_settings`, `sanitize_redirect` open-redirect guard defaulting to `/crm`). Client (vanilla JS, NOT frappe.ui) POSTs stock `/api/method/login` and handles EVERY state: `"Logged In"`→redirect; `"No App"`→treat as success→/crm; `"Password Reset"`→follow `redirect_to`; **`verification`+`tmp_id` → MFA step: persist tmp_id, render prompt from `verification{method,prompt,setup,token_delivery}`, re-POST `{otp,tmp_id}` to same endpoint.** Support all 3 methods (OTP App incl. first-time QR/`setup===false`, SMS, Email), wrong/expired-OTP recovery, social (suppress in OIDC flow), LDAP. **DO NOT override the `login`/`logout` whitelisted methods — only shadow the page.** context7-validated contract: `/frappe/frappe` `auth.py`+`twofactor.py`. **Proof (recorded): a 2FA (OTP App) user logs in end-to-end; repeat for SMS + Email; parity spot-check vs stock `/login`.**
- **E2-S4 — graceful logout + branding helper.** SPA + pages → stock `/api/method/logout` then `/login?redirect-to=`. Add `crm/branding.py` (`get_configured_app_brand()` + `apply_brand_context(context,brand,surface=)`) reading FCRM Settings; call from all www pages. Proof: clean-session walkthrough root→login→app→access-restricted→logout with ZERO stock Frappe screens.

### E3 — Public landing page (Sprint 3, depends on E1 tokens)
- **E3-S1** `crm/www/index.{py,html}` — plain Jinja, modeled on `careverse_hq/www/index.html` re-skinned to Tiberbu red/black/white; `no_cache`; redirect-if-logged-in→`/crm`; `no_header`/`no_breadcrumbs`; hero + tagline "Powering Better Health" + CTAs. Proof: logged-out branded screenshot, no stock chrome.
- **E3-S2** Demo CTA → real CRM Lead via existing public form engine (`crm/www/crm_form.py`, `crm/api/form.py`). Proof: submit → Lead appears in list.

### E4 — Telephony platform + Avaya forms (Sprint 1, NO external dep — ship forms so credential handoff is turnkey)
Pattern reference: existing `crm/integrations/exotel/` + `crm/fcrm/doctype/crm_exotel_settings`. Anchors verified: `crm/integrations/api.py` — `_get_recording_credentials()` (L11), `is_call_integration_enabled()` (L33); `crm/fcrm/doctype/crm_call_log/crm_call_log.json` `telephony_medium` options `"\nManual\nTwilio\nExotel"` (L152); `frontend/src/components/Telephony/CallUI.vue` provider refs (L2-3, provider list L67-68, `setMakeCall` L129).
- **E4-S1** New Single doctype `CRM Avaya Settings` — `enabled`, `mode` (Select: `Cloud (AXP)`/`On-Prem (Aura/AES)`, gates fields via `depends_on`), `record_calls`, `webhook_verify_token`; Cloud fields (`axp_base_url`, `axp_region`, `client_id`, `client_secret`=Password, `account_id`); On-Prem fields (`aes_host`, `cti_user`, `cti_password`=Password, `dmcc_or_tsapi_link`, `cm_id`, `recorder_base_url`, `recorder_auth`=Password, `connector_endpoint`). All secrets = `Password` fieldtype. Proof: settings form screenshot both modes, no creds.
- **E4-S2** Extend `crm_call_log.json` L152 enum → add `\nAvaya` (+ update `CRMCallLog` type Literal in `.py`); `crm_telephony_agent` add `avaya_number` + `Avaya` in `default_medium`. Proof: JSON diff + form shows Avaya.
- **E4-S3** Register Avaya in `is_call_integration_enabled()` + `_get_recording_credentials()` (returns "not connected" cleanly with no creds). New `frontend/src/components/Telephony/AvayaCallUI.vue` (mirror `ExotelCallUI.vue`) + register in `CallUI.vue`. Proof: API dump shows Avaya present/disabled.

### E5/E6 — Avaya CONNECT (Sprint 4, GATED on Tiberbu Avaya credentials — see `avaya-integration-prd.md` §9)
- **E5 (Cloud/AXP first — closest to Exotel):** new `crm/integrations/avaya/handler.py` mirroring `exotel/handler.py` — `@frappe.whitelist(allow_guest=True) handle_request` (webhook, token-validate, `frappe.publish_realtime("avaya_call", …)`, create/update CRM Call Log, `get_contact_by_phone_number` for screen-pop), `make_a_call` (AXP REST outbound). Recording via existing `get_recording_url` proxy.
- **E6 (On-Prem Aura/AES):** same handler, `mode=="On-Prem"` — needs a server-side CTI connector bridging AES (TSAPI/DMCC) events → same webhook path.
- **Do NOT invent Avaya API payloads as real** — they're discovery items; build against confirmed contracts from the Avaya team.

### E7 — Support-journey automation (Sprint 5, needs E4/E5 call events)
Compose existing primitives (no new engine): SLA (`CRM Service Level Agreement`), core `Assignment Rule`, `scheduler_events` in hooks, `CRM Notification`. Onboarding journey = new **explicit** `CRM Deal` doc_event (NOT `on_update` side-effect). Missed-call recovery hangs off Avaya call-log status.

---

## 6. Per-story workflow (do this every time)

1. Grep existing patterns before writing (codebase is source of truth).
2. context7 for any frappe/frappe-ui/library API before relying on it (re-check against INSTALLED version — v16.17.4 here; 2FA internals especially).
3. Implement as a vertical slice; keep shared-file edits to minimal, marked lines (fork-safety).
4. Verify: frontend → `cd frontend && yarn build` (must pass) + browser screenshot light AND dark; backend → `bench --site cr-dev.tiberbu.app migrate` + `bench restart` + request/response proof.
5. Second-pass review: data-shape mismatches, dead code/unused imports, null/falsy-zero (`?? ` not `||` when 0 valid), API contract, dark/light parity.
6. Attach proof; set story to `review` (NEVER `done` — user promotes).
7. Do NOT commit/push unless the user explicitly says so. Never `git add -A`.

---

## 7. Open decisions / watch-outs

- **Fork sync risk:** the `_add`→`add` fix proves upstream/Frappe drift will bite. On any `git merge upstream/develop`, re-run install on cr-dev + the E2 walkthrough as a smoke test; scan for private `frappe.*` imports.
- **Avaya edition unknown** (BRD R1) — E5/E6 gated until Tiberbu confirms live edition + credentials (send `avaya-integration-prd.md`).
- **Compliance** (BRD R2): call-recording consent/retention + Kenya DPA 2019 before recording go-live.
- **Brand assets:** need official Tiberbu logo SVG + canonical hex confirmation (using `#bc1823` from tiberbu.com live CSS as interim).
- `home_page="index"` precedence must be tested against existing users' `default_workspace` behavior before merge.
