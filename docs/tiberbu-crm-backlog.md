# Tiberbu CRM — Prioritized Story Backlog

**Companion to:** [BRD](./tiberbu-crm-brd.md) · [Internal PRD](./tiberbu-crm-prd.md) · [Avaya Integration PRD](./avaya-integration-prd.md)
**Status:** living backlog · **Date:** 2026-07-29
**Discipline (BMAD posture):** one story = one vertical slice = one proof; stories stop at `review`; agents never set `done`; mandatory second-pass review; context7 re-checked at build.

Priority = value × (1 / dependency-risk). Sprint 1 is everything with **no external dependency** (immediate brand impact + the surfaces users see first). Avaya *connect* work waits on Tiberbu credentials but its *forms* (E4) do not.

---

## Sprint 1 — Brand & first impressions (no external dependency)

| ID | Story | Epic | Proof | Status |
|---|---|---|---|---|
| **E1-S1** | Remap the interactive **blue accent → Tiberbu red** via CSS-variable override (light + dark); neutrals (black/white) untouched | E1 | Build passes; before/after screenshots of links/selection/focus in both themes | in-progress |
| **E1-S2** | Re-skin brand mark (`CRMLogo.vue` magenta → Tiberbu red/logo) + app title + PWA manifest | E1 | Screenshot of logo/tab title; manifest diff | pending |
| **E1-S3** | Set runtime brand (`FCRM Settings` brand_name/logo/favicon = Tiberbu CRM) + document it | E1 | Screenshot of sidebar/header showing Tiberbu brand | review |
| **E1-S4** | Hardcoded-hex sweep (ThemeSwitcher dots, rating stars, event-color defaults, geolocation) for brand consistency; preserve semantic status colors | E1 | `grep '#[0-9a-fA-F]{3,8}'` report + screenshots | review |
| **E4-S1** | New `CRM Avaya Settings` (Single) doctype — dual-mode fields (AXP + Aura/AES), secrets as Password, `mode` toggle | E4 | Screenshot of settings form, both modes; no creds entered | review |
| **E4-S2** | Extend `CRM Telephony Agent` (`avaya_number` + `Avaya` in `default_medium`) & `CRM Call Log` (`Avaya` in `telephony_medium`) | E4 | DocType JSON diff + form screenshot showing Avaya option | review |
| **E4-S3** | Register Avaya in `is_call_integration_enabled` + `_get_recording_credentials` (returns "not connected" cleanly with no creds) | E4 | API response dump showing Avaya present, disabled | review |

## Sprint 2 — Native-surface suppression & auth (no external dependency; highest complexity)

| ID | Story | Epic | Proof | Status |
|---|---|---|---|---|
| **E2-S1** | `hooks.py`: `home_page="index"`, `/login` route rule, `before_request` guard registered; verify no regression to `/crm` routing or `default_workspace`-on-login | E2 | Guest hits `/` → landing; logged-in `/` → SPA (screenshots) | review |
| **E2-S2** | `crm/api/route_guard.py` desk fence (werkzeug 303) + branded `www/access-restricted` page; deny-by-default allow-list | E2 | Non-allow-listed user → `/app` → branded 401; allow-listed → desk | review |
| **E2-S3** | Branded `www/login` page — **full Frappe auth parity incl. MFA** (OTP App/SMS/Email, tmp_id re-POST, password-reset, social, LDAP) — BRD §5.3.1 hard gate | E2 | **Recorded**: 2FA user logs in end-to-end (all 3 methods); parity spot-check vs stock `/login` | review |
| **E2-S4** | Graceful logout → branded `/login?redirect-to=`; `branding.py` helper shared by all www pages | E2 | Clean-session walkthrough: zero stock Frappe screens | review |

## Sprint 3 — Public landing page (depends on E1 tokens)

| ID | Story | Epic | Proof | Status |
|---|---|---|---|---|
| **E3-S1** | `www/index` public landing — careverse_hq structure re-skinned to Tiberbu theme; redirect-if-logged-in → SPA | E3 | Logged-out branded screenshot (no stock chrome) | review |
| **E3-S2** | Landing **Request-a-demo CTA → real CRM Lead** via existing public form engine | E3 | Submit CTA → Lead appears in list (round-trip) | review |

## Sprint 4 — Avaya connect (GATED: Tiberbu Avaya credentials, BRD R1)

| ID | Story | Epic | Proof | Status |
|---|---|---|---|---|
| **E5-S1** | Avaya **Cloud (AXP)** handler: inbound webhook → realtime `avaya_call` → screen-pop + call log | E5 | Inbound call screen-pops matched record; call logged | blocked (Avaya creds) |
| **E5-S2** | AXP click-to-dial (`make_a_call`) + recording URL stored + playback via existing proxy | E5 | Outbound call logged with playable recording | blocked (Avaya creds) |
| **E5-S3** | `AvayaCallUI.vue` registered in `CallUI.vue` provider list | E5 | Call UI appears when Avaya enabled | review (built in E4-S3) |
| **E6-S1** | Avaya **On-Prem (Aura/AES)** connector bridging CTI → same webhook path (`mode=On-Prem`) | E6 | Call logged via AES path with recording | blocked (Avaya creds) |

## Sprint 5 — Support-journey automation (depends on E4/E5 for call events)

| ID | Story | Epic | Proof | Status |
|---|---|---|---|---|
| **E7-S1** | Onboarding journey: won Deal → staged tasks + assignment + SLA reminders (explicit doc_event, not on_update side-effect) | E7 | Test Deal won → tasks + assignment + SLA timer fire | review |
| **E7-S2** | Missed-call recovery: missed Avaya call → callback task + SLA + notification | E7 | Simulated missed call → task + notification | review |

---

## Dependency graph
```
Sprint 1 (E1 brand, E4 Avaya forms) ─┬─► Sprint 3 (E3 landing needs E1 tokens)
Sprint 2 (E2 auth/native) ───────────┘
                              Sprint 4 (E5/E6 Avaya connect)  ◄── GATED: Avaya creds
                              Sprint 5 (E7 journeys)          ◄── needs E4/E5 call events
```

## Notes
- **Sprint 1 + 2 can run in parallel** (independent surfaces). Sprint 1 first for visible brand progress.
- Every frontend story: verify `yarn build` + dark/light before `review`.
- Every backend story: `bench restart` (Python not hot-reloaded); whitelisted methods carry type annotations.
- Fork-safety check per story: shared-file edits kept to marked minimal lines.
