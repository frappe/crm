---
project_name: 'crm'
user_name: 'Salim'
date: '2026-08-01'
status: 'active'
---

# Project Context — Tiberbu CRM

_Critical rules and patterns that AI agents must follow when implementing code in this project._

---

## What this project is

A fork of `frappe/crm` — Vue 3 + frappe-ui frontend, Frappe Python backend. Branded as
Careverse CRM for Tiberbu. Runs at `cr-dev.tiberbu.app` (dev) and `crm.tiberbu.app` (prod).

Key customisations over upstream:
- AWS SES outbound override (no IMAP mailbox required for sending)
- SES inbound pipeline (SNS push → Communication creation)
- Avaya telephony integration (E4)
- Partner portal API (in progress)
- Tiberbu brand tokens, desk access guard, branded login/landing

---

## Environment

- **Site:** `cr-dev.tiberbu.app`
- **App path:** `/home/ubuntu/frappe-bench/apps/crm`
- **Branch:** `careverse_fixes` → remote `upstream` (https://github.com/tiberbu/crm.git)
- **Base branch:** `develop`
- **Python:** 3.11+ via bench env at `/home/ubuntu/frappe-bench/env/bin/python`
- **Frontend:** Vue 3 + frappe-ui, built with Vite, output to `crm/public/frontend/`
- **Frappe version:** v15

---

## Technology Stack

- **Backend:** Frappe v15, Python 3.11, MariaDB
- **Frontend:** Vue 3, frappe-ui, Vite, Tailwind
- **Email outbound:** AWS SES (`crm.email.ses_send` via `override_email_send` hook)
- **Email inbound:** AWS SES → SNS → `crm.api.ses_inbound.receive` webhook
- **Telephony:** Avaya E4 integration (`crm.integrations.avaya`)
- **AWS region (outbound):** eu-west-2
- **AWS region (inbound):** eu-west-1 (SES receiving not available in eu-west-2)

---

## Mandatory: context7 before every framework decision

Before writing any Vue, Frappe Python, frappe-ui, or Vite pattern — no exceptions:

1. `mcp__context7__resolve-library-id` → map the library to a context7 ID
2. `mcp__context7__query-docs` → fetch current docs

Covers: Vue 3, frappe-ui, Vite, Frappe v15, TanStack Query, Tailwind, boto3.
If context7 is unreachable → block and surface it. Never fall back to training memory.

## Mandatory: BMAD discipline for all work

All work follows the BMAD pipeline:
1. **Plan** — epic + stories written in `_bmad-output/<epic>/planning-artifacts/` before any code
2. **Stories** — reviewed against `STORY-RULES.md`, mapped to a BRD section
3. **Implement** — worker dispatched from Studio to `implementation-artifacts/` workdir
4. **Review** → **QA** → **Done** — `sprint-status.yaml` updated at each gate
5. **Never set `done`** — agents stop at `review`. Salim promotes.

No code written without a story. No story without a BRD. No BRD without a planning session.

---

## Critical Implementation Rules

### Python / Frappe
- **`bench restart` after every Python change** — no exceptions, Python changes are never hot-reloaded.
- **`bench migrate` after every DocType JSON change** — fields won't exist in the DB otherwise.
- `frappe.get_list()` for all user-facing reads. Never `frappe.db.sql()` for SELECTs.
- `ignore_permissions=True` only on scheduler/webhook/system-internal paths — add `# SYSTEM-INTERNAL` comment.
- `on_update` hooks banned for side effects — use explicit API calls or scheduler jobs.
- Email via `frappe.sendmail()` only. Never raw boto3 SMTP.
- Never use f-strings in log/error message strings — Amazon Inspector flags them as XSS (B608).
  Use `%`-formatting: `"bucket=%s key=%s" % (bucket, key)` or explicit string concat.

### SES Override (critical)
- `override_email_send` fires AFTER `CrmSesAwareEmailQueue` skips `fetch_outgoing_server()`.
  Do NOT add any code that calls `get_email_account()` before the override check.
- The QueueBuilder patch (`crm.email.queue_patch`) is applied at hooks.py module-import time.
  If you add a new hooks.py import that fails, the patch silently doesn't apply.
- `get_ses_runtime_config()` is cached per-request in `frappe.local.flags`.
  After saving CRM SES Settings, call `clear_ses_runtime_config_cache()`.

### Vue / Frontend
- `createResource` must be declared at setup time with `onSuccess`/`onError` — never inline inside a function.
- No drawers or modals for primary work surfaces — full-page views only.
- Dark/light mode parity mandatory — no hardcoded hex colours.
- `pnpm build` must pass with zero errors before PR.

### Security
- No f-strings in log/error strings (Amazon Inspector B608 — XSS false positive but kills PR checks).
- Inbound email body must be escaped with `frappe.utils.escape_html()` before HTML wrapping.
- SNS signature must be verified on every inbound webhook — never skip in production.
- No `.bandit` suppression files — comply instead of suppressing.

---

## Key Files

| File | Role |
|------|------|
| `crm/hooks.py` | App hooks — SES patch applied at module-import, override_email_send wired |
| `crm/email/ses_runtime.py` | AwsSesRuntimeConfig dataclass + per-request cache |
| `crm/email/ses_send.py` | `override_email_send` transport — SES v1/v2 + native fallback |
| `crm/email/email_queue.py` | CrmSesAwareEmailQueue — skips fetch_outgoing_server when SES enabled |
| `crm/email/queue_patch.py` | QueueBuilder monkey-patch for bulk-send path |
| `crm/email/ses_inbound_provision.py` | Idempotent boto3 script — S3, SNS, SES receipt rules |
| `crm/api/ses.py` | get_settings / update_settings whitelisted API |
| `crm/api/ses_inbound.py` | SNS webhook handler — sig verify, MIME fetch, Communication creation |
| `crm/api/ses_inbound_provision_api.py` | Whitelisted provision wrapper — saves ARNs back to settings |
| `crm/fcrm/doctype/crm_ses_settings/` | CRM SES Settings Single DocType |
| `frontend/src/components/Settings/SESSettings.vue` | SES Settings UI |

---

## BMAD Output Structure

```
_bmad-output/
  sprint-status.yaml          ← source of truth for story state
  STORY-RULES.md              ← story definition standards
  project-context.md          ← this file
  ses-inbound/
    planning-artifacts/       ← epics, stories, WIs
    implementation-artifacts/ ← workdir for Studio workers
    proof/                    ← screenshots, API dumps, test output
  partner-portal/
    planning-artifacts/
    implementation-artifacts/
    proof/
```

Worker `workdir` for Studio = `_bmad-output/<epic>/implementation-artifacts/`

---

## Active Epics

| Epic | Status | BRD |
|------|--------|-----|
| ses-inbound | Code done, DevOps pending | `ses-inbound/planning-artifacts/WI-DevOps-AWS-Provisioning-2026-08-01.md` |
| partner-portal | Ready for dev | `partner-portal/planning-artifacts/` (BRD: `docs/partner-portal-brd.md`) |
