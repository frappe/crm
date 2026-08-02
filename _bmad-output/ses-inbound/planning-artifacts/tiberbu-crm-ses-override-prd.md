# Tiberbu CRM — Native SES Email Override PRD (v2 — brownfield rebuild)

**Discipline:** BMAD — one story = one vertical slice = one proof; stops at `review`; agents never set `done`; mandatory second-pass; context7-checked.
**Date:** 2026-08-01
**Author:** Salim
**Supersedes:** the outbound-transport portion of `tiberbu-crm-ses-email-spec.md` (2026-07-30). The inbound-threading analysis in that doc still stands.
**Site under test:** `cr-dev.tiberbu.app`
**Verification recipient:** `salim@tiberbu.com`

---

## 0. Why this PRD exists (the honest post-mortem)

The previous SES work (commits `bbf1437` → `f6f8e00`) **did not work** and the invitation flow still errors with:

> Please setup default outgoing Email Account from Tools > Email Account

This PRD documents the proven root cause, then specs a native rebuild that makes `frappe.sendmail` — and every other Frappe send surface — route through AWS SES via **CRM SES Settings**, with no dependency on any other app.

### Root cause — proven, not assumed

Diagnostic run on `cr-dev.tiberbu.app` (`bench console`):

```
installed_apps: ['frappe', 'erpnext', 'crm']
override_email_send hook: ['frappe_devsecops_dashboard.email.aws_ses_override.send']
override_doctype_class[Email Queue]: ['frappe_devsecops_dashboard.email.email_queue_override.AwsSesAwareEmailQueue']
QueueBuilder patched flag: False
get_outgoing_email_account func: frappe.email.doctype.email_queue.email_queue   ← STOCK, unpatched
runtime cfg enabled: True | sender: careverse-sales@tiberbu.com | region: eu-west-2
```

Reproduction:

```
frappe.sendmail(recipients="salim@tiberbu.com", subject="…", message="…", now=True)
→ OutgoingEmailError: Please setup default outgoing Email Account from Tools > Email Account
```

**The defect:** the entire working SES send stack lives in `frappe_devsecops_dashboard`, **which is not installed on `cr-dev`**. The CRM's `hooks.py` (commit `bbf1437`) declares:

```python
override_email_send = "frappe_devsecops_dashboard.email.aws_ses_override.send"
override_doctype_class = { "Email Queue": "frappe_devsecops_dashboard.email.email_queue_override.AwsSesAwareEmailQueue" }
```

Those two hooks resolve (the modules are importable on disk), **but the decisive piece — the `QueueBuilder` monkeypatch** (`get_outgoing_email_account` / `send_emails`) — is applied only by **devsecops's own `hooks.py` top-level import**:

```python
# frappe_devsecops_dashboard/hooks.py — never imported on cr-dev because the app isn't installed
apply_queue_builder_patches()
```

Frappe's send pipeline is: `sendmail()` → `QueueBuilder` builds the Email Queue doc → **during build it calls `get_outgoing_email_account()`** to resolve the sender, HTML wrapper, and signature → stock `find_outgoing(_raise_error=True)` throws because no Email Account exists → the send dies **before** `override_email_send` is ever reached.

So the primed config (`crm.email.ses_config.prime_ses_config`, correctly enabled) is read by nobody. The prior implementation was a façade over an uninstalled app.

### The three failure classes this PRD fixes

1. **Structural (E1):** SES send logic must live in and be wired from **CRM itself** — the `QueueBuilder` patch, the `override_email_send` target, and the `Email Queue` subclass — so the override fires on any site with only `crm` installed.
2. **Semantic (E2):** the CRM SES Settings UI must match the backend contract — the "Email Account" inbound field is a free-text `Data` on the frontend but a `Link` in the DocType; the sync silently no-ops on mismatch. And the "does Email Account work with SES?" question is answered: **no native Email Account is needed for outbound** once E1 lands.
3. **Identity (E3/E4):** dynamic sender name + image-capable user signatures.

---

## 1. Architecture decision (locked)

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Transport** | Port the boto3 SES API stack **into CRM** (`crm/email/`), wired from `crm/hooks.py`. Uses `ses:SendRawEmail`. | Chosen over SES-SMTP-via-Email-Account: reuses the AWS access-key/secret already stored in CRM SES Settings (SES SMTP needs *different*, IAM-derived credentials), keeps region/retry/configuration-set config meaningful, and fixes the exact bug with zero new AWS setup. |
| **Sender name fallback** | `{User full name} from {brand}` (e.g. *Salim from Careverse Team*) when Default Sender Name is blank; brand-only for system/scheduler sends with no user context. | Human, on-brand, and degrades safely. |
| **Dependency on devsecops** | **Removed entirely.** CRM owns every override. | The root cause. Non-negotiable. |

### Does the stock Email Account work with SES? (answering the user's Q2)

- **Outbound:** After E1, **no Email Account is required.** CRM's `QueueBuilder` patch supplies a synthetic in-memory Email Account (sender identity from CRM SES Settings) so the queue builds, and `override_email_send` ships the MIME bytes to SES via boto3. Stock Frappe Email Account relies on SMTP/Frappe Mail — SES's API path is not SMTP, which is exactly why the override + synthetic account is the correct customization.
- **Inbound:** unchanged — inbound still needs a real, pollable Email Account (IMAP). SES inbound (Receipt Rule → S3/SNS) is out of scope here and remains as analysed in the prior spec. The inbound fields in CRM SES Settings continue to mirror onto a real Email Account.

### Target send path (after E1)

```
frappe.sendmail(...)                      # unchanged call sites everywhere
  └─ QueueBuilder.build()
       └─ get_outgoing_email_account()    # CRM PATCH: SES on → synthetic account (no throw)
  └─ EmailQueue doc created
  └─ AwsSesAwareEmailQueue.send()          # CRM subclass: SES on → skip SMTP fetch
       └─ override_email_send → crm.email.ses_send.send(queue, sender, recipient, mime)
            └─ boto3 ses.send_raw_email(...)  # From rewritten to CRM SES sender identity
```

When SES is **disabled**, every patch falls through to stock behaviour (native SMTP/Frappe Mail) — no regression for non-SES installs.

---

## 2. Context7 validation

| Claim | Source | Verified |
|-------|--------|----------|
| `frappe.sendmail(...)` signature (sender, reply_to, now, template, args, message_id, in_reply_to) | `/frappe/frappe` v16 `frappe/email/__init__.py` | ✓ |
| `override_email_send` is the per-recipient outbound transport hook; called from `EmailQueue.send` with `(queue_doc, sender, recipient, message)` | `/frappe/frappe` v16 `email_queue.py` + `get_hook_method("override_email_send")` | ✓ |
| Sender/HTML/signature are resolved **at queue-build time** via `QueueBuilder.get_outgoing_email_account()` → `EmailAccount.find_outgoing(_raise_error=True)`; this is where the error is thrown | `email_queue.py:725`, `email_account.py:499,523` | ✓ |
| v16: `frappe.sendmail` no longer implicitly commits — caller must commit | Frappe "Migrating to version 16" | ✓ (relevant to `now=True` invitation path) |
| Signature append: `get_signature(email_account)` only fires for a real account with `add_signature`; user signature is prepended client-side via `crm.api.get_user_signature` | `email_body.py:550`, `CommunicationArea.vue:155` | ✓ |
| frappe-ui `TextEditor` supports images via `uploadFunction` prop + `InsertImage` toolbar button; neither is wired in the current signature editor | `/frappe/frappe-ui` editor API; `UserEmailSettings.vue:39` | ✓ |

---

## 3. Epics & Stories

Legend — each story is one vertical slice with one proof. Agents stop at `review`.

### E1 — Native outbound SES override (owned by CRM)

> **Goal:** `frappe.sendmail` delivers via SES on a site with only `crm` installed. Fixes the invitation error.

#### E1-S1 — Port the SES runtime config + send target into CRM
- **Change:** create `crm/email/ses_runtime.py` (the `AwsSesRuntimeConfig` dataclass + `get_ses_runtime_config()` cache, reading **CRM SES Settings**, self-contained — no import from devsecops). Create `crm/email/ses_send.py` (the `send()` override target: boto3 `send_raw_email` / `send_email` by payload size, `From` rewrite, native fallback when disabled). Delete the parasitic `crm/email/ses_config.py` prime-shim and its `before_request` hook entry.
- **Wiring:** `crm/hooks.py` → `override_email_send = "crm.email.ses_send.send"`.
- **Proof:** `bench console` — with SES enabled, `get_ses_runtime_config().enabled is True` and `send`'s module is `crm.email.ses_send`; no reference to `frappe_devsecops_dashboard` resolves in any CRM email hook.

#### E1-S2 — Port the QueueBuilder patch + Email Queue subclass into CRM
- **Change:** create `crm/email/queue_patch.py` (`apply_queue_builder_patches()` patching `get_outgoing_email_account` → synthetic account when SES on, `send_emails` to skip eager SMTP resolution) and `crm/email/email_queue.py` (`AwsSesAwareEmailQueue`). Apply the patch from `crm/hooks.py` at import (guarded, idempotent, `_PATCH_FLAG`). Wire `override_doctype_class["Email Queue"] = "crm.email.email_queue.AwsSesAwareEmailQueue"`.
- **Synthetic account** carries the CRM SES sender identity and, critically, `add_signature`/`signature` support so E3-S2 (user signature) still works.
- **Proof:** `bench console` — `getattr(QueueBuilder, "_crm_ses_decoupler_patched") is True` and `QueueBuilder.get_outgoing_email_account.__module__ == "crm.email.queue_patch"`.

#### E1-S3 — Green the invitation send (the reported bug) — **primary acceptance**
- **Change:** none beyond E1-S1/S2; this story is the end-to-end proof.
- **Proof:** on `cr-dev`, invite a user (or `frappe.sendmail(recipients="salim@tiberbu.com", ..., now=True)`) → **no `OutgoingEmailError`** → SES `MessageId` logged → **email received at salim@tiberbu.com**. Capture the console result + the SES success log line. This is the story that was failing.

#### E1-S4 — Disabled-mode + no-regression guard
- **Change:** ensure every patch falls through to stock when `enabled=0`.
- **Proof:** flip SES off in CRM SES Settings → `sendmail` uses stock `find_outgoing` (errors only if no Email Account, i.e. stock behaviour) → flip on → SES resumes. Document both console runs.

### E2 — Fix the CRM SES Settings UI ↔ backend contract

#### E2-S1 — Inbound "Email Account" field: free-text → Link picker
- **Defect:** `SESSettings.vue` renders `inbound_email_account` as `type="text"` (free text); the DocType field is `Link → Email Account`; `_sync_inbound_email_account` no-ops unless the string exactly equals an existing Email Account name. Silent failure.
- **Change:** replace the free-text `FormControl` with the CRM `Controls/Link.vue` component bound to `doctype="Email Account"` (pattern already used in `DefaultsSettings.vue`, `PreferencesSettings.vue`). Keep the helper text.
- **Proof:** screenshot — typing shows an Email Account autocomplete; selecting one and saving round-trips (reload shows the saved link); dark + light mode.

#### E2-S2 — Sender identity validation + inline "why" copy
- **Change:** when SES enabled, require Sender Email (SES-verified) client-side before save; add a one-line note that no native Email Account is needed for outbound once SES is on.
- **Proof:** screenshot — save blocked with a clear message when Sender Email is blank while enabled.

### E3 — Sender identity & signatures

#### E3-S1 — Dynamic Default Sender Name fallback
- **Change:** in `crm/email/ses_send.py` `From`-rewrite, when CRM SES Settings `default_sender_name` is blank, compose the display name from the eligible session user's full name + a team label (new optional `sender_team_label` field on CRM SES Settings; falls back to FCRM Settings `brand_name`). Never overrides an explicitly-set Default Sender Name.
- **Graceful degradation (required — no "Salim from None"):** the team label is only appended when it resolves to a real, non-empty value. The resolver strips whitespace and rejects the literal strings `"none"`/`"null"` (case-insensitive) as well as empty. Cascade:
  - user + valid team → `"Salim from Careverse Team"`
  - user, no valid team → `"Salim"` (bare full name, **never** `"Salim from None"`)
  - no user (system/scheduler) + valid team → `"Careverse Team"`
  - neither → no display name; send with the bare verified sender email.
- **DocType:** add `sender_team_label` (Data, optional) to CRM SES Settings + expose in `SESSettings.vue` + `api/ses.py` get/update whitelist.
- **Proof:** `bench console` — with blank sender name, send as a user → captured MIME `From:` reads `Salim from Careverse Team <careverse-sales@tiberbu.com>`; send with no session user → `Careverse Team <…>`.

#### E3-S2 — Preserve user email signature under SES
- **Change:** confirm the synthetic Email Account (E1-S2) does not strip the client-prepended signature (`CommunicationArea.vue` → `get_user_signature`), and that `add_signature`/`signature` on the synthetic account behave. No behavioural change intended; this is a guard + proof story.
- **Proof:** send a Lead email from the CRM UI with a configured signature → received email at salim@tiberbu.com shows the signature intact.

### E4 — Image-capable user signature (item 4)

#### E4-S1 — Enable image upload in the signature editor
- **Finding (context7-verified):** frappe-ui `TextEditor` supports images via the `uploadFunction` prop + `InsertImage` toolbar button. The current signature editor (`UserEmailSettings.vue:39`) passes **neither**, so image signatures cannot be inserted today.
- **Change:** wire `:uploadFunction` (Frappe file upload → returns `file_url`) and add `InsertImage` to the signature editor's fixed menu. Store the resulting `<img src>` HTML in `User.email_signature` (Text Editor field — already HTML-capable).
- **Consideration:** inline `<img>` with an absolute site URL renders in received mail; verify the src is absolute (or embed as inline image) so external clients load it. Spec whether to upload-as-attachment-and-cid vs. absolute URL — **default: absolute public URL** for simplicity, flag CID as a follow-up if images are blocked.
- **Proof:** screenshot — insert an image into the signature, save, reload (persists); then send a test email to salim@tiberbu.com → received mail shows the image.

---

## 4. Files touched (map)

| File | Epic | Action |
|------|------|--------|
| `crm/email/ses_runtime.py` | E1-S1 | **new** — self-contained config dataclass + cache (reads CRM SES Settings) |
| `crm/email/ses_send.py` | E1-S1, E3-S1 | **new** — `override_email_send` target (boto3), From rewrite + dynamic sender name |
| `crm/email/queue_patch.py` | E1-S2 | **new** — QueueBuilder patch + synthetic account |
| `crm/email/email_queue.py` | E1-S2 | **new** — `AwsSesAwareEmailQueue` subclass |
| `crm/email/ses_config.py` | E1-S1 | **delete** — parasitic prime-shim |
| `crm/hooks.py` | E1 | rewire `override_email_send`, `override_doctype_class`, drop `prime_ses_config` from `before_request`, add `apply_queue_builder_patches()` at import |
| `crm/fcrm/doctype/crm_ses_settings/crm_ses_settings.json` | E3-S1 | add `sender_team_label` |
| `crm/api/ses.py` | E2, E3 | expose `sender_team_label`; keep password-safe contract |
| `frontend/src/components/Settings/SESSettings.vue` | E2, E3 | Link picker for inbound account; sender validation; team-label field |
| `frontend/src/components/Settings/Profile/UserEmailSettings.vue` | E4 | `uploadFunction` + `InsertImage` in signature editor |

---

## 5. Non-goals

- SES inbound receipt (Receipt Rule → S3/SNS). Inbound stays IMAP-pull via a real Email Account.
- Migrating any devsecops site off its existing stack. This is CRM-scoped only.
- Multi-tenant per-user SES identities beyond the on-domain sender rewrite.

---

## 6. Risks & mitigations

| Risk | Mitigation |
|------|-----------|
| Monkeypatching `QueueBuilder` at hooks import — order/idempotency | Guard with `_PATCH_FLAG`; wrap in try/except with logging (mirror the proven devsecops guard); patch is a pure pass-through when SES disabled. |
| Both CRM **and** devsecops installed on the same bench later → double patch | Idempotent flag + patch-once; last-writer both point at equivalent logic. Document that CRM's is authoritative for CRM sends. |
| SES `From` not verified in AWS → send rejected | E2-S2 requires a verified Sender Email; surface SES `MessageRejected` in the error log with the address. |
| v16 no-commit change for `sendmail` | Invitation path uses `now=True`; verify the `email_sent_at` db_set still commits (it's a separate `db_set`). |
| Image signature blocked by recipient mail client | Default absolute public URL; note CID-embed follow-up. |

---

## 7. Test plan (all on `cr-dev.tiberbu.app`, recipient `salim@tiberbu.com`)

1. **E1-S3 (primary):** invite-user flow / direct `sendmail(now=True)` → received at salim@tiberbu.com, SES MessageId logged, no OutgoingEmailError.
2. **E1-S4:** toggle SES off → stock path; on → SES path.
3. **E2-S1:** Link picker round-trip screenshot (dark+light).
4. **E3-S1:** MIME `From:` = "Salim from Careverse Team <…>" (blank sender name) and brand-only for system send.
5. **E3-S2:** Lead email with signature received intact.
6. **E4-S1:** image inserted in signature → persisted → visible in received mail.

**Proof rule:** no story moves to `review` without its artifact (console dump / screenshot / received-mail confirmation). Mandatory second-pass review (data-shape, dead code, null/falsy-zero, contract, dark/light) before `review`.
