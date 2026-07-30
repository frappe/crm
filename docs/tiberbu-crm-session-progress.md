# Tiberbu CRM — Session Progress (2026-07-30)

Continues the handoff (`tiberbu-crm-handoff.md`). This session drove the backlog from
E1-S3 through E7, plus documented the gated E5/E6. **Nothing committed or pushed.**

## Status board

| Story | State | Proof doc |
|---|---|---|
| E1-S1, E1-S2 | done (prior session) | handoff §2 |
| **E1-S3** runtime brand | review | `tiberbu-crm-runtime-brand.md` |
| **E1-S4** hex sweep | review | `tiberbu-crm-hex-sweep.md` |
| **E2-S1..S4** native-surface + auth (MFA parity) | review | `tiberbu-crm-native-surface-suppression.md` |
| **E3-S1** landing | review | `tiberbu-crm-landing-and-avaya-forms.md` |
| **E3-S2** demo CTA → Lead | review | ″ |
| **E4-S1..S3** Avaya forms + api + UI | review | ″ |
| **E5-S3** AvayaCallUI registered | review (built in E4-S3) | `tiberbu-crm-avaya-connect-status.md` |
| **E7-S1, E7-S2** support automation | review | `tiberbu-crm-support-automation.md` |
| **E5-S1/S2, E6-S1** Avaya connect | blocked (Avaya creds) | `tiberbu-crm-avaya-connect-status.md` |

All `review` per BMAD posture — **agents never set `done`; Salim promotes.**

## Second-pass review (mandatory, RULES §5) — done, findings fixed

Two `frappe-code-reviewer` passes ran (E2; E4+E7). Outcome: **CHANGES REQUIRED → all
addressed.**

- **E2 BLOCKER 1** — desk-fence bypass: a workspace-having System User at `/` got the
  native desk before `index.py` ran. Fixed with a `pin_home_page_to_landing`
  `before_request` (forces `/`→index). Verified: `BYPASS? false`.
- **E2 BLOCKER 2** — forced-password-reset stripped the reset `key`. Fixed by whitelisting
  `/update-password` in both redirect guards. Verified key survives; open-redirect still closed.
- **E2 nits** — Website-User "No App" → `/access-restricted` (not stock 403); removed dead
  login context vars + per-request LDAP read.
- **E4** — `webhook_verify_token` → Password (was plaintext Data); `_get_recording_credentials`
  made mode-aware (Cloud uses AXP `client_secret`, On-Prem uses `recorder_auth`); dropped
  unused import.
- **E7** — journey bodies moved to `frappe.enqueue` (legit `ignore_permissions` path, no
  save latency); fires on create-as-Won; missed-call falls back to owner when `receiver`
  empty; distinct notification `from_user`; dropped invalid `"Missed"` status.
- **Noted, not changed:** the `_add`→`add` assign import (crm_deal/crm_lead) is the
  pre-existing documented fork-fix (handoff §2); reviewer flagged the public-`add()`
  notification side-effect — left per "keep it" instruction.

Final 7-check E2 walkthrough: **7 passed, 0 failed.** Frontend `yarn build` green.

## New files this session (additive — fork-safe)

- `crm/branding.py`
- `crm/api/route_guard.py`
- `crm/www/{index,login,access_restricted}.py` + `{index,login,access-restricted}.html`
- `crm/public/images/tiberbu-mark.svg`
- `crm/fcrm/doctype/crm_avaya_settings/` (json + py + __init__)
- `crm/automation/support_journey.py` + `__init__.py`
- `frontend/src/components/Telephony/AvayaCallUI.vue`
- `docs/brand/tiberbu-logo.png`, `docs/brand/tiberbu-favicon.png`
- `docs/tiberbu-crm-*.md` (this + 5 story docs)

## Marked minimal core edits (watch on upstream merge)

- `crm/hooks.py` — `home_page`, `/login` route rule, `before_request` guard (E2); `CRM Deal.on_update` + `CRM Call Log` doc_events (E7)
- `crm/www/crm.py` — guest → branded login (E2-S4)
- `crm/integrations/api.py` — Avaya branches (E4-S3)
- `crm/fcrm/doctype/crm_call_log/{json,py}` — `Avaya` enum (E4-S2)
- `crm/fcrm/doctype/crm_telephony_agent/{json,py}` — `avaya_number` + `Avaya` (E4-S2)
- `frontend/src/components/Telephony/CallUI.vue` — AvayaCallUI registration (E4-S3)
- Frontend re-hue edits (E1-S4): RatingInput, GeolocationControl, Event*/Calendar*, ThemeSwitcher

## Environment state on cr-dev (dev-only, reversible)

- FCRM Settings brand populated (E1-S3): brand_name "Tiberbu CRM" + logo/favicon Files.
- Published Web Form `request-a-demo` (→ CRM Lead) for the landing CTA.
- `System Settings.setup_complete = 1` set to reach desk (ERPNext still shows its own
  setup wizard — no Company; unrelated to CRM).
- Test fixture user `sales.tester@tiberbu.test` (Sales User) for the desk-fence + MFA
  proofs; 2FA toggled on during the MFA test then **restored to disabled**. **Remove the
  test user + demo Leads before any prod cut.**
- `desk_access_users` NOT set → only Administrator reaches the desk.
- Dev server: `bench --site cr-dev.tiberbu.app serve --port 8005` (log `/tmp/crm-serve.log`).
- Proof screenshots: `/tmp/crm-proof/` (e2-*, e3-*, e4-*, s4-*, brand-*).

## Not committed

`git status` shows all the above as modified/untracked. Stage by name only when Salim
gives the go-ahead; never `git add -A`.

## Next

- Salim promotes reviewed stories to `done`.
- Send `docs/avaya-integration-prd.md` to Tiberbu Avaya team to unblock E5/E6.
- Compliance (Kenya DPA 2019) review before enabling call recording.
- Optional polish: replace interim `tiberbu-mark.svg` with official brand SVG; i18n copy
  pass ("Welcome to Frappe CRM" onboarding string).
