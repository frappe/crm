# Business Requirements Document — Tiberbu CRM

**Product:** Tiberbu CRM (a customized fork of Frappe CRM)
**Sponsor:** Tiberbu — *Powering Digital Health in Kenya*
**Document status:** Draft v0.1 — for review before PRD
**Date:** 2026-07-29
**Author:** Salim

---

## 1. Document purpose

This BRD defines the *business* requirements for customizing the open-source Frappe CRM into **Tiberbu CRM** — the commercial and customer-support layer that wraps the **Careverse HMIS** product. It states the problems, the users, the use cases, and the success criteria. It intentionally stops short of implementation detail; the architecture and detailed designs move into the PRD after this document is reviewed and aligned.

Two things make this a *brownfield* effort rather than a greenfield build:

1. We are forking an actively-maintained upstream (`frappe/crm`) and must **retain the ability to pull upstream changes indefinitely**. Every customization decision is judged against that constraint.
2. The base product is mature — SLAs, assignment rules, telephony (Twilio/Exotel), lead capture, and a Vue 3 frontend already exist. We are *extending and re-skinning*, not rebuilding.

> **Scope note / correction:** the frontend is **Vue 3 + frappe-ui + Tailwind CSS**, not React/Ant Design. All theming requirements below are expressed in those terms.

---

## 2. Business context & vision

### 2.1 Who Tiberbu is
Tiberbu builds **Careverse**, a FHIR-ready Health Information Management System (HMIS) for the Kenyan market — powering the Primary Care Network (PCN) model, with eCitizen and telemedicine integration. Brand identity is **red / black / white** (verified primary red `#bc1823`), tagline *"Powering Better Health."*

### 2.2 The problem
Tiberbu sells, onboards, and supports Careverse across hospitals, clinics, and PCN networks. Today the **commercial pipeline** (prospecting facilities, demos, deployment deals) and the **customer-support journey** (onboarding a new facility, resolving tickets, handling support calls) are not managed in one system. Support calls in particular are handled on an **Avaya** contact-centre platform that is disconnected from any customer record — calls aren't logged against the account, aren't recorded against a case, and journeys aren't automated.

### 2.3 The vision
A single, Tiberbu-branded CRM that:
- Presents an **intuitive, on-brand landing page** and a fully **red/black/white themed** application.
- Manages the **B2B/B2G sales journey** for Careverse (facility → deal → deployment).
- Manages the **customer-support journey** for live Careverse customers (onboarding, SLAs, tickets, escalations).
- **Integrates with Avaya** so every customer call is click-to-dialled, screen-popped, recorded, and logged against the right account — and support journeys are automated (routing, follow-ups, SLA-driven reminders).

### 2.4 Why Frappe CRM as the base
It already ships the primitives this vision needs: Leads/Deals, Contacts/Organizations, a **pluggable telephony layer** (Twilio + Exotel today — Avaya is a third provider following the same pattern), **Service Level Agreements**, **Assignment Rules**, notifications, a public lead-capture web-form engine, and a themeable Vue frontend. This dramatically de-risks delivery: most requirements map to *configuration + extension* rather than net-new engineering.

---

## 3. Goals & success metrics

| # | Business goal | Success metric (target) |
|---|---|---|
| G1 | On-brand first impression | Public landing page live; ≥1 primary CTA (request demo / log in); passes brand review (red/black/white, tiberbu logo). |
| G2 | Consistent Tiberbu identity across the app | 100% of primary-action UI renders in Tiberbu red; no stray default-magenta/blue accents; dark **and** light mode both on-brand. |
| G3 | Unified customer record | 100% of Avaya support calls auto-logged against a Contact/Organization/Deal with a playable recording. |
| G4 | Faster, SLA-tracked support | First-response SLA measured and met on ≥90% of support interactions. |
| G5 | Journey automation | Onboarding & support journeys auto-assign, auto-notify, and auto-escalate without manual routing. |
| G6 | Fork maintainability | Able to merge upstream `frappe/crm` releases with **zero core-file conflicts** in the customization layer. |

---

## 4. Fork & maintainability strategy (foundational constraint)

This governs *how* every requirement is implemented.

- **Upstream topology.** `upstream = tiberbu/crm` (already a fork of `frappe/crm`); `frappe-ui` is a git submodule tracking `frappe/frappe-ui`. The last sync merged `frappe:develop`. We keep syncing.
- **Golden rule — additive over invasive.** Prefer *new files* (new integration module, new route component, new settings doctype, appended CSS variables) over editing shared core files. Where a core file must change (e.g. adding `"Avaya"` to an enum), keep the diff minimal and semantically obvious so it survives 3-way merge.
- **Theming without forking components.** frappe-ui exposes colors as **semantic CSS variables / Tailwind tokens** (`--surface-*`, `--ink-*`, `--outline-*`) — verified against frappe-ui docs. Re-skinning is done by **overriding those variables in app CSS**, never by editing `node_modules` or component internals.
- **Never** bypass hooks, force-push shared branches, or create branches without sign-off (per team rules).
- **Definition of "fork-safe":** a `git merge upstream/develop` applies cleanly against the customization layer, or conflicts only in the handful of intentionally-marked enum/registration lines.

---

## 5. Immediate requirements (the two named deliverables)

### 5.1 Requirement A — Intuitive landing page

**Business need:** a public, on-brand entry point that communicates Tiberbu CRM's value and routes visitors to log in or request a demo — styled consistently with the CRM app's own look and feel.

- **A1.** A **public (logged-out) landing page** served at a guest-accessible route, rendered **outside** the authenticated app shell, with Frappe's stock web header/breadcrumbs stripped.
- **A2.** Visual language: **match the `careverse_hq` landing/login/unauthorized surfaces** (the sibling app in this bench that already replaced all native Frappe web surfaces) **but re-skinned to the CRM/Tiberbu theme** — red/black/white, frappe-ui typography scale, rounded surfaces — so landing, auth pages, and the app read as one product. See Requirement C (§5.3) and §13 for the mechanism.
- **A3.** Tiberbu branding: logo, red/black/white palette, tagline ("Powering Better Health").
- **A4.** Clear primary CTA(s): **Log in** (into the CRM) and **Request a demo / Contact us** — the latter feeding the existing public lead-capture form so a landing visitor becomes a CRM Lead.
- **A5.** Responsive (desktop + mobile). Landing/auth surfaces follow the careverse_hq convention of a single fixed (light) brand treatment; the *app* remains dark/light-aware.
- **A6.** **RESOLVED — logged-out public page.** It doubles as a marketing + lead-capture surface. A logged-in visitor hitting the landing route is redirected straight into the CRM SPA (mirrors careverse_hq's `index.py` redirect-if-authenticated). Only the landing/auth routes are guest-exposed; all CRM *data* stays authenticated.

**Acceptance (business-level):** a logged-out visitor lands on a Tiberbu-branded page (no stock Frappe chrome), understands what Tiberbu CRM is, and can either sign in or submit a demo request that appears as a Lead in the CRM; a logged-in visitor is bounced into the app.

### 5.2 Requirement B — Tiberbu color scheme across the app

**Business need:** the entire application reflects Tiberbu's red/black/white identity, in both light and dark mode, without breaking usability or upstream-merge safety.

- **B1.** Primary/action color = Tiberbu red (`#bc1823` family; accent `#ff5538` available for highlights). Black/near-black and white already form the base palette.
- **B2.** Interactive elements currently rendered in the default blue (links, checkboxes, selection) re-hued to the Tiberbu scheme.
- **B3.** Brand mark updated from the default (magenta placeholder) to the Tiberbu logo; app name/title/favicon/PWA manifest updated to "Tiberbu CRM."
- **B4.** Status colors (success green, error red, warning) preserved for *semantic* meaning — the re-skin must not make "error red" and "brand red" indistinguishable in a way that harms comprehension. (Design nuance for PRD.)
- **B5.** Dark **and** light mode both verified on-brand.
- **B6.** Implemented via the token/CSS-variable override layer (fork-safe), with the option to expose `brand_name` / `brand_logo` / `favicon` through the existing runtime **settings** so non-developers can adjust branding without a deploy.

**Acceptance (business-level):** across landing, list views, detail pages, buttons, and dialogs, the product reads as Tiberbu — verified by side-by-side screenshots in both themes, with no off-brand accent colors.

### 5.3 Requirement C — No native Frappe surfaces; CRM frontend is the default route

**Business need:** end users must **never** see a stock Frappe surface — not the native login, not the desk landing, not the logout page, not a raw "insufficient permission" error. The bare domain must resolve to the Tiberbu CRM experience, and every auth/error surface must be branded. The Frappe desk (`/app`) remains reachable **only** for the small set of technical users who explicitly need it.

This is a *known, solved problem in this bench*: the sibling app **`careverse_hq`** already replaced every native Frappe web surface. Tiberbu CRM will **replicate that exact mechanism**, re-skinned to the CRM theme, so the two apps stay consistent and the approach is proven.

- **C1 — Default route.** The bare domain / site root resolves to the Tiberbu CRM experience: a **guest** sees the branded landing page; an **authenticated CRM user** is taken into the CRM SPA. No stock Frappe portal or desk home is ever the default.
- **C2 — Branded login with FULL auth-flow parity (incl. MFA).** `/login` serves a Tiberbu-branded login page (not Frappe's stock login) that is a **complete, faithful reimplementation of Frappe's entire login flow — not just the happy path.** It authenticates against the **standard** `/api/method/login` endpoint and correctly handles **every** state Frappe returns, so behavior is identical to stock Frappe (only the styling differs). This explicitly includes multi-factor authentication handled **exactly** as Frappe does it. Detailed contract in **§5.3.1** — this is a hard acceptance gate.
- **C3 — Graceful logout.** Logout returns the user to the branded `/login` (with a safe redirect back into the CRM), never a stock Frappe logout/blank page.
- **C4 — Branded unauthorized page.** Any access-denied condition (including a non-privileged user attempting to reach the desk) routes to a branded **"Access Restricted"** page with clear next actions (go to CRM / sign out) — never a raw Frappe permission error.
- **C5 — Desk fenced, not removed.** `/app` (Frappe desk) stays available to an explicit allow-list of technical/admin users (a "switch to desk" affordance for them). Everyone else attempting a desk path is redirected to the branded unauthorized page. Desk access is **deny-by-default**; the allow-list is the source of truth.
- **C6 — Fork-safe.** All of the above is achieved by *additive* app-level files (page shadows in `www/`, a `before_request` route guard, `home_page` + `website_route_rules` in `hooks.py`) — **no edits to Frappe core** and no override of the stock `login`/`logout` API methods — so it survives upstream `frappe/crm` and Frappe framework merges. (Mechanism detail in §13.)

**Acceptance (business-level):** starting from a clean browser session, a user can reach the site root, log in, use the CRM, hit an access-restricted condition, and log out — and at **no point** sees an unbranded/stock Frappe screen. A non-privileged user navigating to `/app` gets the branded Access Restricted page; an allow-listed admin reaches the desk.

#### 5.3.1 Custom login must fully reimplement Frappe's auth flow, MFA included (hard requirement)

**The risk this closes:** the common failure of a custom login page is to reimplement only "username + password → success" and silently drop everything else — 2FA, password-expiry, social login, LDAP, "no app" — locking out any user with MFA enabled or leaving them on a broken/stock screen. **That is unacceptable here.** The Tiberbu login page must reproduce Frappe's **entire** `/api/method/login` state machine so it is functionally indistinguishable from stock Frappe, differing only in styling. The proven `careverse_hq` login is the reference implementation (it already handles the full flow); the Frappe contract below is context7-validated against `/frappe/frappe` (`auth.py`, `twofactor.py`).

The custom page **must** call the standard `/api/method/login` (POST, `credentials: same-origin`, `X-Frappe-CSRF-Token` header, CSRF token seeded server-side into the page) and correctly branch on **every** documented response:

- **`message: "Logged In"`** → session established; redirect to the sanitized `redirect-to` (or the CRM default).
- **`message: "No App"`** → treat as a successful login (Frappe returns this when the user has no default app) and route into the CRM.
- **`message: "Password Reset"`** → the account is forced to reset (expired/`force_user_to_reset_password`); follow Frappe's `redirect_to` to the reset flow — do **not** treat as a failure.
- **MFA / 2FA challenge — the critical path.** When Frappe returns a **`verification` object + `tmp_id`** (and `message` is *not* "Logged In"), the page must transition into a **verification step** and complete the second factor **exactly** as Frappe's own login does:
  - **Persist `tmp_id`** (careverse_hq stores it in a `tmp_id` cookie *and* in memory) and **re-POST to the same `/api/method/login`** with `{ otp, tmp_id }` — the OTP is confirmed by Frappe's `confirm_otp_token` against the cached secret; there is no separate endpoint.
  - Support **all three Frappe verification methods** driven by System Settings `two_factor_method`: **OTP App** (TOTP/authenticator — including the first-time QR-provisioning-via-email case where `setup === false`), **SMS**, and **Email**. Render the method-appropriate prompt from the `verification` object (`method`, `prompt`, `setup`, `token_delivery`).
  - Honor the delivery/setup signals: if `token_delivery === false` (SMS/email send failed) or `setup === false` (first-time OTP App), show the correct guidance rather than a dead OTP box — as careverse_hq's `canProceedWithVerification` / `getVerificationPrompt` do.
  - Handle **expired challenge** (`"Login session expired, refresh page to retry"`) and **incorrect code** by letting the user retry / restart cleanly (clear the stale `tmp_id`).
  - Respect Frappe's own 2FA behaviors — Administrator exemption, role-based enablement, and restricted-IP bypass are enforced server-side; the page must not assume 2FA is always on or always off, but react to what `/api/method/login` returns.
- **Social / OAuth login** (`provider_logins` from `get_oauth2_providers()`) rendered as provider buttons — and suppressed during the OIDC provider-authorize flow, per careverse_hq.
- **LDAP** login honored when `LDAP Settings` is enabled.
- **System-setting gates** respected: `disable_signup`, `disable_user_pass_login`, `login_with_email_link`, and the login label (Email / Username / Mobile per `allow_login_using_*`).
- **Open-redirect safety:** the `redirect-to` param is sanitized (block external netlocs, force internal-prefixed paths, default unknowns into the CRM) — reuse careverse_hq's `sanitize_redirect` allow-list approach.
- **`update-password` / reset** and the `/qrcode` provisioning page must remain reachable and branded (or at minimum functional) so the reset and first-time-OTP journeys aren't dead ends.

**Acceptance (hard gate — must be proven before this story leaves `review`):**
1. A user **with 2FA (OTP App) enabled** logs in fully through the branded page: password → authenticator code → CRM. Proof: screen recording/screenshots of both steps + landed-in-CRM.
2. The same, proven for **SMS** and **Email** 2FA methods (per `two_factor_method`).
3. **First-time OTP App enrollment** (QR/email provisioning, `setup === false`) is handled — user can enroll and complete login, not stuck.
4. **Password-expired** account is routed to reset (not shown as a login error).
5. Wrong OTP and expired `tmp_id` produce clear, recoverable errors — no lockout, no stock Frappe screen.
6. Social (if a provider is configured) and LDAP (if enabled) paths function.
7. Behavior parity spot-check: the branded page and Frappe's stock `/login` accept the same credentials and reach the same authenticated state for a 2FA user.

> **Context7 obeyed:** the Frappe auth/2FA contract above (`message` states, `verification`/`tmp_id`, `confirm_otp_token`, the three verification methods, Administrator/role/IP rules) is validated against `/frappe/frappe` `auth.py` + `twofactor.py`. Implementation must re-verify against the *installed* Frappe version at build time, since 2FA internals can shift between releases.

---

## 6. Strategic requirements (the "why" behind the customization)

These frame the roadmap the two immediate deliverables sit inside. They are stated here as business intent; the PRD will scope phasing.

### 6.1 Careverse customer-journey management
Model and manage the full lifecycle of a Careverse customer: **Prospect facility → Qualified lead → Deal/Deployment → Onboarding → Live support**. Sales owns the left of that funnel; Customer Success/Support owns the right. The CRM must represent both, on the same account record, with stage-appropriate automation (SLAs, assignment, notifications, follow-ups).

### 6.2 Avaya telephony integration
Every inbound/outbound customer call flows through Avaya but is **surfaced and recorded inside the CRM**:
- **Click-to-dial** from a Contact/Lead/Deal.
- **Screen-pop** on inbound calls — the agent sees the matched customer record before answering.
- **Automatic call logging** against the right account, with call type, status, duration, and a **playable recording**.
- **Support-journey automation** driven by call outcomes (e.g. missed call → task + SLA timer; resolved call → journey stage advance).

*Feasibility signal:* telephony in Frappe CRM is a proven **pluggable multi-provider platform** — Twilio and Exotel each implement webhook → realtime-popup → shared `CRM Call Log` (which already has a `recording_url` and an authenticated recording-streaming proxy). Each provider is independently enable-able, and each agent has a per-user `default_medium` selecting which provider dials on their behalf (confirmed via context7 against `/frappe/crm`). **Avaya becomes a third provider on the same rails**, not new architecture.

#### 6.2.1 Avaya dual-mode support (on-prem *and* cloud) — design decision

Avaya is not one product but two integration families, and Tiberbu wants **both** supported behind a togglable setting:

- **On-prem — Avaya Aura.** Integrated via CTI: Application Enablement Services (AES) with TSAPI/DMCC/JTAPI. Call events and call control arrive over a CTI link; recordings come from an on-prem recorder (e.g. Avaya Contact Recorder / ACR) referenced by URL. Typically requires a server-side connector/bridge inside the Tiberbu network.
- **Cloud — Avaya Experience Platform (AXP).** Integrated via REST APIs + webhooks and cloud media/recording URLs — architecturally the closest match to the existing Exotel pattern (server webhook in, REST call out, recording URL stored).

**Requirement:** ship a single **"Avaya" provider with a `mode` toggle (`On-Prem (Aura/AES)` | `Cloud (AXP)`)** in its settings, so an administrator picks the deployment without code changes. Both modes converge on the *same* `CRM Call Log` record shape, the same screen-pop realtime event, and the same recording-playback proxy — only the connector/credentials behind the toggle differ.

**Platform framing (broader intent):** rather than hard-coding a third provider, treat telephony as a **provider-agnostic integration platform**: Twilio, Exotel, and Avaya (On-Prem / Cloud) all appear as *selectable, individually-togglable options* under one Telephony settings surface, with a per-agent default medium. This makes future providers (or additional Avaya editions) additive and keeps the fork mergeable. New providers are *registered*, not wired in ad hoc.

> **Honesty flag (context7 scope):** the *Frappe* provider/registry and call-log model above are context7-validated (`/frappe/crm`, `/frappe/frappe-ui`). Avaya's own vendor APIs (AES/TSAPI/DMCC, AXP REST/webhooks, recorder auth) are **not** a context7-indexed library; their exact contracts are **PRD-discovery** items, gated on confirming Tiberbu's live Avaya edition(s) — see Risk R1. Nothing about Avaya vendor endpoints in this BRD should be treated as verified API detail.

#### 6.2.2 Avaya integration-readiness — all forms in place before credentials arrive

**Requirement (explicit):** build the Avaya integration so that **every form/field an administrator needs to connect Avaya is present and shipped**, and the day Tiberbu's Avaya credentials are made available, connecting is a **fill-in-the-blanks configuration task — no new development, no schema change, no deploy**. The credentials are the *only* missing input; the scaffolding waits for them.

This mirrors the existing providers exactly. Twilio and Exotel each ship a Single **settings DocType** (an admin form) plus fields on the per-agent **CRM Telephony Agent** form; Avaya must ship the equivalent, covering **both** modes (§6.2.1). Concretely, the following forms must exist and be reachable before credentials arrive:

- **`CRM Avaya Settings` (Single DocType — the admin connection form).** Fields sized to cover both editions, with the `mode` toggle gating which are relevant:
  - `enabled` (Check) — the platform toggle that lists Avaya alongside Twilio/Exotel.
  - `mode` (Select: `Cloud (AXP)` | `On-Prem (Aura/AES)`) — drives which fields below apply (via `depends_on`).
  - **Cloud (AXP) fields:** API base URL / region, client ID, **client secret (Password)**, account/tenant ID, webhook verify token, `record_calls` (Check).
  - **On-Prem (Aura/AES) fields:** AES host, CTI/TSAPI or DMCC service credentials (**Password** for secrets), CM/link identifiers, recorder (ACR) base URL + auth (**Password**), connector/bridge endpoint if used.
  - Following the Exotel/Twilio precedent, every secret uses the **`Password`** fieldtype (encrypted at rest), and a `webhook_verify_token`-style shared secret guards the inbound webhook.
- **`CRM Telephony Agent` (existing form — extend, don't replace).** Add an `avaya_extension` / `avaya_number` field (mirroring `exotel_number` / `twilio_number`) and add **`Avaya`** to the `default_medium` Select (today `Twilio` / `Exotel`) so an agent can be assigned to dial via Avaya. The existing `phone_nos` child table and `call_receiving_device` (Computer/Phone) are reused as-is.
- **`CRM Call Log` (existing form — extend enum).** Add **`Avaya`** to the `telephony_medium` Select so Avaya calls log against the same record shape (from/to, type, status, duration, `recording_url`, dynamic links to Lead/Deal/Contact/Task/Note) already used by the other providers.
- **Provider registration / discovery.** Avaya must appear in the telephony platform's enabled-integrations response (what the frontend reads to decide which call UIs to offer) and in the recording-credentials resolver (so recording playback authenticates correctly per mode) — so that once `enabled` is checked and credentials entered, the CRM call UI, screen-pop, and recording playback light up without further code.

**Readiness acceptance (business-level):** with **no credentials entered**, an administrator can open **CRM Avaya Settings**, see all fields for both modes, toggle `mode`, and see `Avaya` offered as a telephony medium on the Telephony Agent and Call Log forms. Entering valid credentials (when Tiberbu provides them) is sufficient to place/receive a logged, recorded call — proven end-to-end at that point, not before. Until then, the forms exist, validate their inputs, and clearly indicate "not yet connected."

> **Scope honesty:** shipping the *forms* is fully in scope now and has **no external dependency**. The *field list above is indicative*, drawn from the existing Twilio/Exotel settings shapes; the exact Avaya field set per mode is finalized in the PRD once the live edition is confirmed (Risk R1). Building the forms early is deliberate — it de-risks the credential handoff — but a form field being present is **not** a claim that the Avaya endpoint behind it is verified.

---

## 7. Users & personas

| Persona | Role | Primary jobs-to-be-done |
|---|---|---|
| **Sales Rep** | Sells Careverse to facilities/PCNs | Work leads/deals, call prospects (via Avaya), log activity, move deals through stages. |
| **Sales Manager** | Owns the commercial pipeline | Pipeline visibility, assignment rules, forecasting, team performance. |
| **Support / Customer Success Agent** | Supports live Careverse customers | Answer/place support calls, resolve issues within SLA, advance onboarding, log every interaction. |
| **Support/Ops Manager (Business owner)** | Owns service quality & journeys | Define SLAs & journeys, monitor first-response/resolution, audit call recordings, report to leadership. |
| **CRM Administrator / Technical** | Configures & extends the platform | Branding, telephony config (Avaya), assignment/SLA rules, integrations, keeping the fork mergeable. |
| **Prospect / Customer (external)** | Facility staff | Discover Tiberbu via landing page, request a demo, be supported. |

---

## 8. Use cases

Grouped by the three audiences called out in the brief: **Sales**, **Business**, **Technical**. Each use case: actor, trigger, outcome, and the platform capability it builds on.

### 8.1 Sales users

- **UC-S1 — Capture a demo request from the landing page.** *Prospect submits the landing CTA form → a Lead is created and auto-assigned to a rep → rep is notified.* Builds on: public web-form engine + Assignment Rules + notifications. (Ties Requirement A to the pipeline.)
- **UC-S2 — Qualify and progress a facility lead.** *Rep works the Lead through statuses, converting to a Deal on qualification.* Builds on: Lead/Deal doctypes, status workflow, org-hierarchy scoping.
- **UC-S3 — Click-to-dial a prospect via Avaya.** *Rep clicks a phone number on a Lead/Deal → Avaya places the call → call is auto-logged with recording against that record.* Builds on: telephony provider (Avaya) + `CRM Call Log`.
- **UC-S4 — Log call outcome & schedule follow-up.** *After a call, rep adds a note/task from the call log; a follow-up task with due date is created.* Builds on: call-log note/task APIs + tasks.
- **UC-S5 — Manager reviews pipeline & forecast.** *Sales Manager views deals by stage/owner/territory and a forecast.* Builds on: dashboard/reporting + forecasting settings.
- **UC-S6 — Auto-assign inbound leads by rule.** *New leads route to reps by territory/round-robin.* Builds on: Assignment Rules.

### 8.2 Business users (Support / Customer Success / Ops)

- **UC-B1 — Screen-pop inbound support call.** *Customer calls the Avaya support line → CRM matches the number → agent sees the account (open deals, past calls, SLA status) before answering.* Builds on: Avaya inbound webhook → realtime popup → phone-number→contact resolver.
- **UC-B2 — Resolve within SLA.** *Interaction starts an SLA timer; first-response and resolution are tracked; breaches are flagged.* Builds on: Service Level Agreement engine (working hours, holidays, priorities).
- **UC-B3 — Onboarding journey for a new Careverse facility.** *Won deal triggers an onboarding journey: staged tasks, owner assignment, and SLA-driven reminders until the facility is live.* Builds on: assignment + SLA + scheduler + notifications (journey orchestration layer — new).
- **UC-B4 — Missed-call recovery.** *A missed inbound support call auto-creates a callback task with an SLA timer and notifies the on-duty agent.* Builds on: call-log status + tasks + notifications.
- **UC-B5 — Audit a call recording.** *Ops Manager opens a logged call and plays the recording to review quality/compliance.* Builds on: `recording_url` + authenticated streaming proxy.
- **UC-B6 — Service-quality reporting.** *Manager reports on call volume, SLA attainment, and journey progression.* Builds on: dashboards + call-log/SLA data.
- **UC-B7 — Multi-channel touchpoints on one timeline.** *Calls, emails, notes, WhatsApp all appear on the account's unified activity timeline.* Builds on: activities API merging call logs + communications.

### 8.3 Technical users (CRM Admin / Integrations)

- **UC-T1 — Apply & maintain Tiberbu branding.** *Admin sets brand name/logo/favicon at runtime and the theme override delivers the red/black/white scheme; branding survives an upstream merge.* Builds on: settings-driven branding + CSS-variable override layer. (Requirement B.)
- **UC-T2 — Configure & toggle telephony providers (incl. Avaya dual-mode).** *Admin sees Twilio, Exotel, and Avaya as individually-togglable options under one Telephony settings surface; for Avaya, picks `On-Prem (Aura/AES)` or `Cloud (AXP)`; maps agents to extensions/numbers; sets each agent's default calling medium.* Builds on: provider-agnostic integration platform + new Avaya settings doctype (with `mode` toggle) + telephony-agent mapping (mirrors existing provider config). See §6.2.1.
- **UC-T3 — Define SLAs & assignment rules.** *Admin configures response-time SLAs, working hours/holidays, and routing rules for sales and support.* Builds on: SLA + Assignment Rule config (no code).
- **UC-T4 — Author journey automation.** *Admin/dev defines onboarding & support journeys (stages, triggers, escalations).* Builds on: scheduler events + doc events + notifications + (new) journey definitions.
- **UC-T5 — Keep the fork current.** *Admin merges a new upstream release; the customization layer applies cleanly.* Builds on: additive customization strategy (§4).
- **UC-T6 — Provision users & permissions.** *Admin onboards sales/support staff with correct roles and hierarchy-scoped record access.* Builds on: CRM roles + org-hierarchy permission scoping.

---

## 9. Scope

### 9.1 In scope (this initiative)
- Public, branded **landing page** (Requirement A).
- Full **Tiberbu red/black/white re-skin**, light + dark (Requirement B).
- **Avaya** telephony provider with a **dual-mode toggle (On-Prem Aura/AES · Cloud AXP)**, delivered as a **togglable option alongside Twilio and Exotel** on a provider-agnostic telephony platform: click-to-dial, screen-pop, call logging, recording playback (§6.2.1).
- **Support-journey automation** built on SLA + assignment + scheduler + notifications.
- Branding/config surfaced to admins where practical.
- Fork-maintainability discipline throughout.

### 9.2 Out of scope (this initiative)
- Building or replacing the **Careverse HMIS** itself — integration touchpoints only.
- Deep **FHIR / clinical data** exchange with Careverse (candidate for a later phase; flagged as a dependency, not a deliverable here).
- Migrating away from Frappe/Vue to another stack.
- Replacing existing Twilio/Exotel providers (they remain; Avaya is added alongside).
- Billing/accounting (available via existing ERPNext integration; not a focus here).

### 9.3 Explicitly deferred / to decide in PRD
All §14 questions are now answered (see §14 Resolutions). What remains for PRD-level discovery — not open business questions, but technical detail:
- Exact Avaya **vendor** API contracts per mode (AES/TSAPI/DMCC for on-prem; AXP REST/webhooks for cloud) and recorder auth — gated on Tiberbu's live edition credentials (Risk R1). *The decision to support both is made; only the wiring is deferred.*
- Depth of Careverse HMIS integration beyond the confirmed phase-1 scope (see §14.3).

---

## 10. Assumptions
- Tiberbu owns/administers its Avaya environment and can grant the API/CTI access and recording access the integration requires.
- The CRM and Avaya can reach each other over the network (webhook callbacks + outbound API calls).
- Tiberbu will provide final brand assets (logo SVG, exact palette confirmation) and approve the landing copy.
- Careverse customer/account data can be represented as CRM Organizations/Contacts (with optional sync).
- We continue on Frappe v15 / the current frontend stack; upstream remains active.

## 11. Dependencies & key risks

| # | Dependency / Risk | Impact | Mitigation |
|---|---|---|---|
| R1 | **Avaya vendor API surface not yet detailed.** Both editions are in scope (§6.2.1), but exact on-prem CTI (AES/TSAPI/DMCC) vs. cloud AXP (REST/webhooks) contracts and recorder auth differ and are unconfirmed against Tiberbu's live environment. | High — blocks Avaya build (not design). | Dual-mode is decided; abstract behind one provider + `mode` toggle. Confirm live credentials/endpoints in PRD discovery. Deliver Cloud (AXP) mode first (closest to the proven Exotel pattern), On-Prem (AES) mode second. |
| R2 | Recording access/compliance (call-recording consent, data residency in Kenya, PHI adjacency). | High — legal. | Confirm recording retention, consent, and access-control requirements before build; recordings are proxied/authenticated, not public. |
| R3 | Upstream merge conflicts if customizations are invasive. | Medium — maintenance cost. | Additive strategy (§4); minimal marked diffs on shared files. |
| R4 | Brand red vs. semantic error-red collision harming UX. | Medium — usability. | Design review reserves a distinct error hue; §5.2 B4. |
| R5 | Careverse HMIS integration depth scope-creep. | Medium — timeline. | Kept out of scope here; treated as a separate phase. |
| R6 | Public (logged-out) landing/login surfaces widen the server's public attack surface. | Medium — security. | Only landing + `/login` are guest-reachable; all CRM data stays authenticated. Login open-redirect guarded (sanitize `redirect-to`, internal-prefix allow-list — per careverse_hq). Desk deny-by-default via the route guard. |
| R7 | Desk fence locks out a legitimate admin (allow-list managed in site config, not roles). | Medium — operability. | Allow-list includes Administrator by default; document how to add technical users; guard re-checks server-side each request; branded page offers "sign out" as an escape. |

## 12. Constraints
- **Stack:** Vue 3 + frappe-ui + Tailwind (frontend); Frappe v15 / Python (backend); MariaDB.
- **Maintainability:** must remain mergeable with `frappe/crm` upstream.
- **Team rules:** no unsanctioned branches; no hook bypass; SLAs on proof-of-work; dark/light parity mandatory; library claims validated via context7.

---

## 13. High-level solution shape (informational — detailed design deferred to PRD)

Provided only to show feasibility and anchor the PRD; not a commitment to specifics.

- **Landing page:** a public web page (`www/index`) rendered outside the authenticated shell with stock chrome stripped (`no_header`/`no_breadcrumbs`), structurally modelled on careverse_hq's landing but re-skinned to the CRM theme; CTA posts to the existing public lead-capture form; logged-in visitors are redirected into the SPA.
- **Native-surface suppression & default route (Req C) — proven careverse_hq pattern, replicated & re-skinned:**
  - `home_page = "index"` in `hooks.py` makes the branded landing the site default (context7-validated: `home_page` overrides Website Settings; guest access is handled *inside* the page's `get_context`, since `allow_guest` isn't a www module property but `no_cache` is).
  - `website_route_rules` maps `/login` → a branded login page and keeps the SPA deep-link catch-all (`/crm/<path>` already exists).
  - **Branded login/logout:** shadow `www/login.*` (filename-shadowing beats Frappe's stock login) posting to the **standard** `/api/method/login`, reimplementing Frappe's **full** auth state machine — `Logged In` / `No App` / `Password Reset`, the **MFA `verification`+`tmp_id`→re-POST `{otp,tmp_id}`** flow across OTP App / SMS / Email, plus social/LDAP and the system-setting gates (§5.3.1). Logout uses the **standard** `/api/method/logout` then returns to the branded `/login?redirect-to=…`. No override of the stock login/logout methods; `careverse_hq`'s login is the reference implementation.
  - **Branded unauthorized + desk fence:** a `before_request` route guard redirects non-allow-listed users away from `/app`/`/desk` to a branded `www/access-restricted` page — using `werkzeug.routing.RequestRedirect(code=303)` (the only redirect that works from `before_request`; careverse_hq documents this after testing that `frappe.Redirect` does not). Desk allow-list is deny-by-default (Administrator + an explicit user list). The unauthorized route shares no prefix with `/app`/`/desk` so the guard can't loop.
  - **Fork-safe:** every piece is an additive app file (`www/` shadows, one `before_request` module, `hooks.py` keys) — no Frappe-core edits.
- **Re-skin:** override the frappe-ui semantic color CSS variables (brand/primary + interactive tokens) in the app's CSS entry; update the logo component and app title/manifest; expose brand fields via settings. Auth/landing pages (plain Jinja/HTML, outside the Vue app) carry their own scoped CSS using the same red/black/white tokens so they match the SPA.
- **Avaya provider (dual-mode, togglable platform option):** a new integration module whose settings doctype carries a `mode` toggle (On-Prem Aura/AES · Cloud AXP), delivering webhook + click-to-dial; `"Avaya"` added to the call-log medium enum and the recording-credentials resolver; agent↔extension mapping; and an Avaya call-UI component registered in the existing provider-agnostic call-UI router — sitting alongside Twilio and Exotel as an individually-enableable option.
- **Journeys:** composed from the existing SLA engine, Assignment Rules, scheduler events, and notifications, with a thin journey-definition layer for stages/triggers.

---

## 14. Resolutions (previously open questions)

All questions from the initial draft are resolved below. Where a resolution still needs Tiberbu's factual input (e.g. live credentials), it is marked **[confirm with Tiberbu]** — a data hand-off, not an undecided design.

1. **Avaya edition → RESOLVED: support BOTH.** On-prem (Aura/AES) **and** cloud (AXP) are in scope, behind one togglable Avaya provider with a `mode` setting, offered alongside Twilio/Exotel on a provider-agnostic platform (§6.2.1). Build order: **Cloud (AXP) first**, On-Prem (AES) second. *[confirm with Tiberbu: live edition(s), API credentials, recorder access — for PRD wiring.]*
2. **Landing page → RESOLVED: public (logged-out).** It doubles as a marketing + lead-capture surface (UC-S1). Only the landing route is exposed; all app data stays authenticated (Risk R6). *[confirm with Tiberbu: final CTA copy + owner.]*
3. **Careverse integration depth → RESOLVED for phase 1: read-only account sync (lightweight).** Represent Careverse customers as CRM Organizations/Contacts; deep FHIR/clinical exchange stays out of scope (§9.2) as a later phase.
4. **Palette → RESOLVED: primary red `#bc1823`, accent `#ff5538`, black `#0e0e0e`/`#000000`, white `#ffffff`** (pulled from tiberbu.com's live CSS). *[confirm with Tiberbu: canonical hex + any secondary brand colors + official logo SVG.]*
5. **Compliance → RESOLVED as a gating requirement, not a blocker to spec.** Call-recording consent, retention, and Kenya data-residency (Kenya Data Protection Act 2019) must be satisfied before recording go-live; recordings remain authenticated/proxied, never public (Risk R2). *[confirm with Tiberbu: retention period + consent policy.]*
6. **Rollout → RESOLVED for this initiative: single tenant (Tiberbu internal CRM).** Multi-tenant across PCN facilities is a future consideration, not this scope.

---

## 15. Delivery discipline (BMAD posture)

This repo has **no BMAD scaffolding today** (no `sprint-status.yaml`, no BMAD config). BMAD discipline is therefore applied as *process posture*, not by inventing a framework:

- **This BRD is a spec artifact at `review` status.** Agents never set `done`; Salim promotes.
- **Status flow:** `ready → in-progress → review → qa → done`. Every story stops at `review` with proof-of-work attached.
- **One story = one vertical slice = one proof.** Split any story whose title carries "and" or spans backend **and** frontend.
- **Proof-of-work before `review`:** UI stories → screenshot (light **and** dark); API/backend → request/response or test output; schema/DDL → query result.
- **Mandatory second-pass review** before `review`: data-shape mismatches, dead code/unused imports, null/falsy-zero guards, API-contract violations, dark/light regressions.
- **Context7 obeyed:** Frappe/frappe-ui claims validated (`/frappe/crm`, `/frappe/frappe-ui`); Avaya *vendor* APIs explicitly flagged as unvalidated PRD-discovery (§6.2.1 honesty flag).
- **Fork-safe or it doesn't ship:** each story is checked against "does `git merge upstream/develop` still apply cleanly?" (§4).

### 15.1 Proposed epics (for PRD decomposition into stories)

| Epic | Slice | Primary proof |
|---|---|---|
| **E1 — Tiberbu re-skin** | CSS-variable brand override (red primary + interactive tokens); logo; title/manifest; settings-driven branding | Screenshots, light + dark, across landing/list/detail/dialog |
| **E2 — Native-surface suppression & default route (Req C)** | `home_page` + `website_route_rules`; `before_request` desk-access guard; branded `www/` shadows for login + access-restricted; graceful logout → `/login`. **Login = full Frappe auth-flow parity incl. MFA (§5.3.1)** — split into its own story given the auth-state complexity. | Clean-session walkthrough: root → login → app → access-restricted → logout, **zero** stock Frappe screens; `/app` blocked for non-allow-listed user. **Plus the §5.3.1 hard gate: a 2FA-enabled user logs in end-to-end (OTP App + SMS + Email) through the branded page** — recorded proof. |
| **E3 — Landing page (Req A)** | Public `www/index` outside app shell; careverse_hq-style structure re-skinned to CRM theme; login + demo-request CTAs → lead-capture form | Logged-out screenshot + a Lead created from the CTA; logged-in visitor redirected into app |
| **E4 — Telephony platform + Avaya forms (Req §6.2.2)** | Provider-agnostic settings surface; `CRM Avaya Settings` (both modes) + Telephony Agent/Call Log enum extensions — **all forms shipped, no creds needed** | Screenshot of Avaya settings form (both modes) + `Avaya` offered as a medium, with no credentials entered |
| **E5 — Avaya Cloud (AXP) connect** | AXP mode wiring: webhook, click-to-dial, call log, recording playback (activates once creds provided) | Inbound screen-pop + outbound call, both logged with playable recording |
| **E6 — Avaya On-Prem (Aura/AES) connect** | Same provider, `mode = On-Prem`; CTI connector + on-prem recorder URL | Call logged via AES path with recording |
| **E7 — Support-journey automation** | SLA + assignment + scheduler + notifications for onboarding & missed-call recovery | SLA timer + auto-assign + escalation demonstrated on a test account |

**Sequencing note:** E1→E4 have **no external dependency** and can proceed now (E4 ships the forms so the credential handoff is turnkey). E5/E6 are gated on Tiberbu's live Avaya credentials (Risk R1); E5 (Cloud) before E6 (On-Prem).

---

*Next step: review this BRD (all §14 items resolved; adds Req C native-surface suppression §5.3, Avaya integration-readiness forms §6.2.2). On sign-off, produce the PRD — architecture, data-model deltas, API contracts, and the E1–E7 story breakdown — building on §13 and §15.1. E1–E4 have no external dependency and can start immediately; the native-surface pattern is proven in the sibling `careverse_hq` app and replicated re-skinned here. Avaya credential handoff (E5/E6) is the only remaining hard dependency, and E4 ships the forms so that handoff is turnkey.*
