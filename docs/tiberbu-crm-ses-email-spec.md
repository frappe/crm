# Tiberbu CRM — AWS SES Outbound Override + Inbound Reply Threading Spec

**Discipline:** BMAD — one story = one vertical slice = one proof; stops at `review`; agents never set `done`; mandatory second-pass; context7-checked.
**Date:** 2026-07-30
**Trigger:** (1) Wire AWS SES as the outbound email transport for the CRM — mirroring what `frappe_devsecops_dashboard` already implements. (2) Understand and spec how inbound email replies to leads/deals are received and threaded, and what the SES-native path for inbound looks like.

**Acceptance test:** Send an email from a CRM Lead record → email is delivered via AWS SES → a reply to that email appears as a Communication on the Lead's activity thread.

---

## Architecture context

### What already exists (frappe_devsecops_dashboard)

The bench already has a complete, tested outbound SES stack in the `frappe_devsecops_dashboard` app:

| Component | File | Role |
|-----------|------|------|
| `AwsSesRuntimeConfig` | `email/aws_ses_config.py` | Frozen dataclass; reads from "AWS SES Settings" Single DocType via `frappe.get_cached_doc` |
| `get_ses_runtime_config()` | same | Per-request cache in `frappe.local.flags`; safe to call many times |
| `send()` | `email/aws_ses_override.py` | Hook target for `override_email_send`; routes per-recipient through SES v1/v2 based on payload size; falls back to native SMTP if SES disabled |
| `_apply_configured_sender()` | same | Rewrites `From` header; promotes `X-CR-Thread-Anchor` → `In-Reply-To`/`References` for MIME email threading |
| `_SyntheticEmailAccount` | `email/ses_email_account_decoupler.py` | Minimal Email Account-like object; allows SES sends without a configured Frappe Email Account |
| `apply_queue_builder_patches()` | same | Monkey-patches `QueueBuilder.get_outgoing_email_account` and `send_emails` once per process |
| `AwsSesAwareEmailQueue` | `email/email_queue_override.py` | Subclass of `EmailQueue`; skips SMTP server fetch in SES mode |
| `AWS SES Settings` | DocType (Single) | Already installed in this bench. Fields: `enabled`, `aws_region`, `default_sender_email`, `default_sender_name`, `configuration_set_name`, `retry_mode`, `total_max_attempts`, `use_explicit_credentials`, `access_key_id`, `secret_access_key`, `session_token` |

The devsecops `hooks.py` wires:
```python
override_email_send = "frappe_devsecops_dashboard.email.aws_ses_override.send"
override_doctype_class = {
    "Email Queue": "frappe_devsecops_dashboard.email.email_queue_override.AwsSesAwareEmailQueue",
}
# at top of hooks.py:
from frappe_devsecops_dashboard.email.ses_email_account_decoupler import apply_queue_builder_patches
apply_queue_builder_patches()
```

### What the CRM has today

- **Zero** `override_email_send` wiring in `crm/hooks.py`.
- **Zero** `override_doctype_class["Email Queue"]`.
- Two `frappe.sendmail()` call sites: `CRMInvitation.invite_via_email()` (invitation email) and `api/event.py::_send_email_notification()` (calendar reminders). Both use `now=True` (direct queue bypass).
- Lead/Deal emails are sent via the standard Frappe desk Communication UI → `EmailQueue` → SMTP. No CRM-specific send path.

### Inbound email today (Frappe native)

Frappe polls every 10 minutes (`cron["0/10 * * * *"]`) against every `Email Account` with `enable_incoming=1`. The `InboundMail` pipeline:

1. Parses `In-Reply-To` header → finds parent `EmailQueue` or `Communication` by `message_id`
2. If found → attaches new `Communication` to the same `reference_doctype`/`reference_name`
3. If not found + Email Account `append_to = "CRM Lead"` → new Lead created from sender
4. CRM hook `on_communication_insert` → `create_lead_from_incoming_email()` (gated by `email_account.create_lead_from_incoming_email` flag)

**Dependency on IMAP/POP3:** Frappe's inbound is pull-based polling. It requires a mailbox that can be polled. SES delivers inbound email via push (Receipt Rules → S3 or SNS) — there is no direct polling bridge.

### Realtime refresh — what actually happens (and the bug)

When a `Communication` document is inserted, Frappe's base `Communication.after_insert()` calls `self.notify_change("add")`. That method calls:

```python
frappe.publish_realtime(
    "docinfo_update",
    {"doc": self.as_dict(), "key": "communications", "action": "add"},
    doctype=self.reference_doctype,    # e.g. "CRM Lead"
    docname=self.reference_name,       # e.g. "CRM-LEAD-00001"
    after_commit=True,
)
```

This fires to the Socket.IO room `doc:CRM Lead/CRM-LEAD-00001` — exactly the room the Lead or Deal page subscribes to via `$socket.emit('doc_subscribe', doctype, docname)` in `Activities.vue`.

The frontend handler in `Activities.vue` is:

```js
function handleDocinfoUpdate({ doc, key }) {
  if (key !== 'comments') return   // ← BLOCKS communications
  all_activities.reload()
  _document.reload()
}
```

**The bug:** `handleDocinfoUpdate` filters on `key !== 'comments'` and returns early for any other key, including `key === 'communications'`. This means:

- When a user **sends** an email from the CRM (creates a sent Communication), `all_activities.reload()` is NOT triggered by the socket event. The activity feed only refreshes because the "send email" action calls `reload.value = true` directly in the Vue component after the API call succeeds.
- When an **inbound reply** arrives (via IMAP polling or SES webhook), Frappe fires the `docinfo_update` with `key: "communications"` — but the CRM frontend silently drops it. The user sees no update until they manually reload the page.

This is the root cause of why inbound emails do not appear in real time on the Lead/Deal activity feed. The fix is a one-line change to `Activities.vue`.

---

## Deployment topology

Both `crm` and `frappe_devsecops_dashboard` are co-installed on the same bench. CRM's `hooks.py` can therefore reference devsecops module paths directly — no code duplication required. This is the preferred approach: one implementation, two apps referencing it.

If CRM is ever deployed standalone (without devsecops), the referenced modules will fail to import and the bench will error on startup. **Risk mitigation:** wrap the devsecops import in a `try/except` and log a clear error if unavailable; document the co-install requirement.

---

## Stories

### SES-OUT-1 — Wire outbound SES to CRM hooks.py

**What:** Add the three devsecops wiring hooks to `crm/hooks.py`, importing from the already-installed devsecops app:

```python
# Top of crm/hooks.py — run once per process
try:
    from frappe_devsecops_dashboard.email.ses_email_account_decoupler import apply_queue_builder_patches
    apply_queue_builder_patches()
except ImportError:
    import logging
    logging.getLogger("crm").error(
        "frappe_devsecops_dashboard not installed — SES QueueBuilder patches not applied. "
        "Install frappe_devsecops_dashboard or CRM emails will fall back to native SMTP."
    )

# ... existing hooks ...

override_email_send = "frappe_devsecops_dashboard.email.aws_ses_override.send"

override_doctype_class = {
    "Contact": "crm.overrides.contact.CustomContact",
    "Email Template": "crm.overrides.email_template.CustomEmailTemplate",
    "Email Queue": "frappe_devsecops_dashboard.email.email_queue_override.AwsSesAwareEmailQueue",
}
```

**Prerequisite:** "AWS SES Settings" DocType must be populated (`enabled=1`, `aws_region`, `default_sender_email`, `default_sender_name`). It is already installed on the bench.

**`bench restart` required** after editing `hooks.py`.

**Proof:**
1. Set `enabled=1` in "AWS SES Settings". Configure a verified SES sender address and AWS region.
2. Open a CRM Lead. Click "Send Email" from the activity feed. Fill recipient, subject, body. Send.
3. Check AWS SES CloudWatch / SES send statistics — the message appears as a `SentMessageCount`.
4. Check the Lead's Communication list — a sent Communication with the email body is present.
5. Check `frappe.log_error` — no `AWS SES Send Failure` error entries.
6. Frappe server log shows `INFO frappe_devsecops_dashboard.aws_ses queue=... recipient=... transport=sesv1 message_id=...`.
7. Screenshot: Lead activity feed showing the sent email thread entry.

---

### SES-OUT-2 — Test transactional email paths (invitation + event reminders)

**What:** The two `frappe.sendmail(now=True)` paths in CRM (`CRMInvitation` and `api/event.py`) bypass `EmailQueue` — they call `frappe.sendmail` which goes through `QueueBuilder.send_emails`. The `apply_queue_builder_patches()` from SES-OUT-1 patches `QueueBuilder.send_emails` so these paths are also routed through SES when enabled.

Verify both paths work end-to-end after SES-OUT-1 is deployed.

**Proof:**
1. Invite a team member via CRM Settings → Team → Invite. The invitation email arrives in their inbox via SES (check SES CloudWatch).
2. Create a calendar Event with a participant and an email reminder. Wait for the scheduler (`bench execute frappe.utils.scheduler.enqueue_events_for_next_hour` to force it), confirm the reminder email is delivered.
3. No `AWS SES Send Failure` log errors.

---

### SES-RT-1 — Fix Activities.vue realtime filter for inbound Communications (Frontend — do first)

**What:** A one-line fix in `frontend/src/components/Activities/Activities.vue`. The `handleDocinfoUpdate` function currently only reacts to `key === 'comments'`, discarding `key === 'communications'`. This means inbound emails (and any other Communication inserts) never trigger an activity reload even though Frappe is broadcasting the correct `docinfo_update` event.

**Current code (line ~596):**
```js
function handleDocinfoUpdate({ doc, key }) {
  if (key !== 'comments') return
  all_activities.reload()
  _document.reload()
}
```

**Fix:**
```js
function handleDocinfoUpdate({ doc, key }) {
  if (key !== 'comments' && key !== 'communications') return
  all_activities.reload()
  _document.reload()
}
```

**Why this is sufficient and correct:**

- `Communication.after_insert()` in Frappe core already calls `self.notify_change("add")`, which calls `frappe.publish_realtime("docinfo_update", {"key": "communications", "action": "add", ...}, doctype=ref_doctype, docname=ref_name, after_commit=True)`.
- The Socket.IO room is `doc:<doctype>/<docname>` — exactly the room `Activities.vue` subscribes to with `$socket.emit('doc_subscribe', props.doctype, props.docname)` on mount.
- `after_commit=True` means the event fires only after the DB transaction commits, so the data is always readable when `all_activities.reload()` fires the fetch.
- `_document.reload()` refreshes the Lead/Deal header fields (e.g. `communication_status` which `on_communication_update` sets to "Open" on inbound receipt).
- No new Python code, no new `publish_realtime` call, no custom event name. The plumbing already works end-to-end; only the frontend filter was wrong.

**What events flow through `docinfo_update`:**

| `key` value | Trigger | CRM interest |
|-------------|---------|--------------|
| `"comments"` | `Comment.after_insert` + `on_update` | Already handled |
| `"communications"` | `Communication.after_insert` (`notify_change("add")`) | **This fix** |
| `"communications"` | `Communication.on_update` (`notify_change("update")`) | Also caught by this fix |
| `"communications"` | `Communication.on_trash` (`notify_change("delete")`) | Also caught — email deleted → feed refreshes |

**Scope of impact:** All Lead and Deal activity feeds for all users simultaneously viewing the same record. When Alice receives a reply on Lead-001 and both Alice and Bob have Lead-001 open, both see the new email appear without reloading.

**Proof:**
1. Open a Lead's activity feed in one browser tab. Open a second browser as a different user on the same Lead.
2. From the first tab: send an email to the Lead's contact address.
3. Using any email client, reply to that email (or directly create a received Communication via the Frappe desk as a test shortcut: create a Communication doc with `sent_or_received="Received"`, `reference_doctype="CRM Lead"`, `reference_name=<lead-name>`).
4. In the second browser tab — **without any manual reload** — the new inbound Communication appears in the activity feed within 1–2 seconds.
5. `pnpm build` passes zero warnings. `tsc --noEmit` clean.
6. Regression: existing comment realtime still works (post a comment, observe instant update on another tab).

---

### SES-IN-1 — IMAP inbound via verified SES-managed mailbox (Phase 1 — recommended first)

**What:** The simplest inbound path that works with the current Frappe IMAP polling infrastructure, requiring no custom webhook code.

Configure an IMAP-accessible mailbox whose inbound delivery is handled by AWS SES Receipt Rules → forward to an IMAP-polled address. Options:
- **Gmail / Google Workspace** with a verified SES sender domain + reply-to routing
- **AWS WorkMail** — fully managed IMAP mailbox integrated with SES Receipt Rules
- **SES + forwarder Lambda** — SES Receipt Rule → Lambda → forwards raw MIME to a polled mailbox

The CRM Email Account is configured as:
- `enable_incoming = 1`
- `email_id` = the polled address (e.g. `crm-inbox@tiberbu.app`)
- `append_to = "CRM Lead"`
- IMAP credentials for the mailbox
- `create_lead_from_incoming_email = 1` (CRM custom field)

**How threading works in this model:**
- Outbound emails from CRM are sent via SES with a `Message-Id` header stored in the `EmailQueue` record.
- Replies from leads carry `In-Reply-To: <that-message-id>`.
- Frappe's `InboundMail.reference_document()` finds the parent `EmailQueue` by `message_id` and attaches the reply Communication to the correct Lead.

**What `_apply_configured_sender()` already does for threading:** When a CRM email is sent via SES, `_apply_configured_sender()` preserves the original `From` address as `Reply-To` when the configured sender differs (e.g. `crm@tiberbu.app` as From, but original sender in Reply-To). The reply from the lead will arrive addressed to the Reply-To address — so the polled mailbox must be able to receive that address.

**Limitation:** 10-minute poll lag. Replies appear in the CRM thread within 10 minutes of receipt. Real-time appearance in the UI requires SES-RT-1 to be implemented first (see below).

**Proof:**
1. Send an email to a test Lead via the CRM activity feed.
2. Reply to that email from an external email client.
3. Within 10 minutes, the reply appears as a `Communication (Received)` on the Lead's activity feed.
4. The Communication is linked to the correct Lead (not a new Lead).
5. With SES-RT-1 applied: the reply appears in the activity feed **immediately** when the user is on the Lead page, with no manual reload.
6. Screenshot: Lead activity feed showing the full thread (sent + reply).

---

### SES-IN-2 — SES inbound webhook for push delivery (Phase 2 — spec only, not implemented)

**What:** A real-time inbound path that replaces polling. AWS SES Receipt Rules deliver inbound email to an SNS topic, which HTTP-POSTs to a CRM endpoint within seconds of delivery.

This story is specced for awareness and future implementation. It is **not** in the current implementation scope — SES-IN-1 (IMAP polling) must prove thread routing first.

#### Architecture

```
Inbound email to crm-inbox@tiberbu.app
    → SES Receipt Rule: action = S3 (Bucket: crm-email-storage, prefix: inbound/)
                      + action = SNS (Topic: crm-inbound-email)  [notification only]
    → SNS HTTP subscription → POST to /api/method/crm.api.email_inbound.receive
        → CRM webhook validates SNS message signature
        → fetches raw MIME from S3 (key comes from SNS notification body)
        → parses MIME with email.parser.BytesParser
        → idempotency check: Communication.message_id already exists? → return 200
        → thread resolution: In-Reply-To → EmailQueue.message_id → Lead/Deal
        → frappe.get_doc("Communication").insert(ignore_permissions=True)
            └── Frappe base Communication.after_insert() fires automatically:
                    notify_change("add") →
                    frappe.publish_realtime(
                        "docinfo_update",
                        {"key": "communications", "action": "add", ...},
                        doctype="CRM Lead",  docname="CRM-LEAD-00001",
                        after_commit=True
                    )
                    → Socket.IO room "doc:CRM Lead/CRM-LEAD-00001"
                    → Activities.vue handleDocinfoUpdate fires (after SES-RT-1 fix)
                    → all_activities.reload() → email appears instantly in feed
```

**No custom `publish_realtime` call needed.** The base Frappe `Communication.after_insert()` already handles broadcasting. The only prerequisite is SES-RT-1 (the frontend filter fix) being deployed.

#### Required new CRM components

1. **`crm/api/email_inbound.py`** — whitelisted API endpoint:
   ```python
   @frappe.whitelist(allow_guest=True)
   def receive():
       # 1. Verify SNS message signature (HTTPS POST from SNS)
       #    — fetch signing cert from SigningCertURL (cache it; it rotates rarely)
       #    — verify using Python's cryptography library or ssl + urllib
       # 2. Handle SNS SubscriptionConfirmation (one-time):
       #    — GET the SubscribeURL to confirm the subscription
       #    — return 200 immediately
       # 3. For Notification type:
       #    a. Parse SNS Message JSON → get S3 bucket + key from ses.receipt.action
       #    b. Fetch raw MIME bytes: s3.get_object(Bucket=bucket, Key=key)["Body"].read()
       #       — reuse _get_boto3_session() from aws_ses_override.py
       #    c. Parse: msg = BytesParser(policy=SMTP).parsebytes(raw_mime)
       #    d. Extract Message-Id, In-Reply-To, From, To, Subject, Date
       #    e. Idempotency: if frappe.db.exists("Communication", {"message_id": msg_id}): return
       #    f. Thread resolution (mirrors InboundMail.reference_document()):
       #       — lookup EmailQueue by message_id matching In-Reply-To
       #       — fallback: lookup Communication by message_id matching In-Reply-To
       #       — fallback: new Lead (if create_lead_from_incoming_email flag set)
       #    g. frappe.get_doc({...}).insert(ignore_permissions=True)
       #       — Communication.after_insert() fires → notify_change("add") → realtime
       #    h. return 200  (SNS expects 200 to avoid retry)
   ```

2. **SNS signature verification utility** — must validate X-Amz-Sns-Message-Signature per AWS spec to prevent spoofed webhook deliveries. Use `urllib.request` to fetch the signing certificate (cached).

3. **S3 MIME fetch** — reuse `_get_boto3_session(config, {})` from `aws_ses_override.py` to get an S3 client; `s3.get_object(Bucket=bucket, Key=key)` where key comes from the SNS notification.

4. **Idempotency guard** — SNS is at-least-once delivery. Check before insert:
   ```python
   if frappe.db.exists("Communication", {"message_id": message_id}):
       return  # already processed
   ```

5. **Thread routing** — mirror `InboundMail.reference_document()` logic:
   - Parse `In-Reply-To` header
   - `frappe.db.get_value("Email Queue", {"message_id": in_reply_to}, ["reference_doctype", "reference_name"])`
   - Fall back to `Communication` lookup
   - Fall back to new Lead creation (if `create_lead_from_incoming_email` flag set on the Email Account)

#### SES-side configuration (AWS console / IaC)

```
Receipt Rule Set: tiberbu-crm-inbound
  Rule: tiberbu-crm-leads
    Recipients: crm-inbox@tiberbu.app
    Actions (in order):
      1. S3: Bucket=tiberbu-crm-emails, Object Key prefix=inbound/
      2. SNS: Topic=arn:aws:sns:<region>:<account>:crm-inbound-email
Receipt Rule Set must be set as Active
```

SNS subscription:
```
Protocol: HTTPS
Endpoint: https://cr-dev.tiberbu.app/api/method/crm.api.email_inbound.receive
```

#### Key decisions deferred to implementation

- **Reply-to address vs. per-deal subaddress:** Using a shared `crm-inbox@tiberbu.app` for all CRM emails means all replies land in the same SNS stream — thread routing depends 100% on `In-Reply-To` header fidelity. Per-deal subaddresses (`reply+<deal-name>@tiberbu.app`) would enable routing even without `In-Reply-To`, but require SES receipt rules matching a wildcard pattern, which SES does support via catch-all rules.
- **Raw email storage lifecycle:** S3 objects should have a lifecycle policy (delete after 30 days) to control storage costs. The Communication doc itself holds the email body, so the S3 object is only needed during processing.
- **Attachment handling:** Large attachments in inbound MIME need streaming from S3; do not load full payload into memory.

**Proof (when implemented):**
1. Send an email to a test Lead. Reply from an external email client.
2. Within 5 seconds of the reply being sent, the CRM Lead activity feed shows the inbound Communication — real-time, no 10-minute lag. This works because `Communication.insert()` fires `after_insert` → `notify_change("add")` → `docinfo_update` → `Activities.vue handleDocinfoUpdate` (with SES-RT-1 applied).
3. SNS delivery log for the CRM endpoint shows `200 OK`.
4. Sending the same email twice (SNS retry simulation) → second delivery is idempotent: no duplicate Communication created.
5. Attachment handling: send a reply with a PDF attachment. The PDF appears in the Communications attachments list in the CRM.

---

## Configuration checklist (for SES-OUT-1 readiness)

Before testing SES-OUT-1, verify all of the following in the Frappe desk:

1. **AWS SES Settings** (desk → Frappe Devsecops Dashboard → AWS SES Settings):
   - `enabled = 1`
   - `aws_region` = e.g. `eu-west-1`
   - `default_sender_email` = a SES-verified address (e.g. `crm@tiberbu.app`)
   - `default_sender_name` = e.g. `Tiberbu CRM`
   - If using IAM role on EC2/ECS: `use_explicit_credentials = 0` (uses instance profile)
   - If using explicit keys: `use_explicit_credentials = 1` + keys filled

2. **SES sandbox:** Verify that the `aws_region`'s SES account is out of sandbox (or that test recipient addresses are verified in the SES console).

3. **boto3 installed:** `pip show boto3` in bench's Python env. If missing: `bench pip install boto3 botocore`.

4. **`bench restart`** after any `hooks.py` change.

---

## Risk register

| Risk | Mitigation |
|------|-----------|
| devsecops not co-installed | `try/except ImportError` guard in hooks.py with clear log message; CRM falls back to native SMTP |
| boto3 not installed | Document in setup instructions; add to `crm/requirements.txt` |
| SES sandbox limits test delivery | Use SES-verified test email addresses or request production access |
| `override_doctype_class["Email Queue"]` conflict if devsecops already registers it | Frappe merges `override_doctype_class` dicts across apps — only the last-loaded app's class wins. Since both apps register the same class, this is safe. Document the load order dependency. |
| Double-patching `QueueBuilder` | `apply_queue_builder_patches()` is idempotent — it checks `_PATCH_FLAG` before patching. Safe to call from both app hooks. |
| Inbound IMAP 10-min lag | Acceptable for Phase 1. Phase 2 (SES webhook) eliminates the lag. |
| SNS at-least-once delivery (Phase 2) | Idempotency guard on `message_id` in `Communication` insert |
| `handleDocinfoUpdate` only handles `'comments'` | Fixed in SES-RT-1 — one-line frontend change. Without this fix, no inbound email ever appears in real time regardless of transport. |
| `Communication.notify_change()` publishes `after_commit=True` | The realtime event fires after DB commit, not during insert. The fetch in `all_activities.reload()` is therefore always consistent — no race condition. |

---

## Implementation order

1. **SES-RT-1** — one-line frontend fix in `Activities.vue`. Unblocks real-time for all inbound emails regardless of transport (IMAP polling or SES webhook). Do this first — it is independent of all other stories and has the highest UX impact for the lowest effort.
2. **SES-OUT-1** — wire hooks.py, restart bench, configure "AWS SES Settings", send test email from Lead. This is the minimum deliverable for the "send email to a lead" acceptance test.
3. **SES-OUT-2** — verify invitation and event-reminder emails route through SES correctly.
4. **SES-SENDER-1** — add `sender_mode` field to "AWS SES Settings" DocType; update `_apply_configured_sender()` to honour per-user identity.
5. **SES-SENDER-2** — add `/api/method/crm.api.ses.get_settings` + `update_settings` whitelisted API.
6. **SES-UI-1** — build the `SESSettings.vue` component and wire it into the Settings shell.
7. **SES-IN-1** — configure IMAP-polled mailbox, verify reply threading works end-to-end (realtime already works via SES-RT-1).
8. **SES-IN-2** — future sprint: SNS webhook for sub-10-second inbound. Only spec here; not implemented until SES-IN-1 is proven stable.

---

## Sender identity — design + stories

### Problem statement

The current `_apply_configured_sender()` in `aws_ses_override.py` **always** overwrites the MIME `From` header with `config.default_sender_email` (the address from "AWS SES Settings"). The original sender is demoted to `Reply-To`. This means every email sent from the CRM — whether by a sales rep, a manager, or a system job — arrives in the recipient's inbox with the same generic sender identity (e.g. `Tiberbu CRM <crm@tiberbu.app>`), losing the personal "sent by Alice" signal that builds prospect trust.

The desired default behaviour: **use the logged-in user's email address as `From`**, if and only if that address is verified in SES. Fall back to `default_sender_email` from "AWS SES Settings" when:
- The user's email is not SES-verified (unknown at request time — SES rejects unverified senders)
- SES is configured in "domain verification" mode and the user's email is on the verified domain (in which case user-from works automatically)
- The admin has explicitly chosen the static fallback mode

### Sender resolution strategy

```
sender_mode = "user_first" (default) | "static"

if sender_mode == "static":
    From = config.default_sender_email   ← current behaviour, unchanged

if sender_mode == "user_first":
    user_email = frappe.session.user email address
    if user_email is not empty and user_email domain == verified SES domain:
        From = "Alice Smith <alice@tiberbu.app>"
        # SES domain verification covers any @tiberbu.app address
        # No Reply-To override needed — From IS the real sender
    else:
        From = config.default_sender_email   ← static fallback
        Reply-To = original sender (already done by current code)
```

**Key SES constraint:** SES requires the `From` address to be either:
- An individually verified email address, OR
- An address on a verified domain (e.g. SES domain identity `tiberbu.app` → any `*@tiberbu.app` is sendable)

The `sender_mode = "user_first"` strategy is therefore safe **only** when domain verification is in use (which is the recommended production setup). The CRM cannot dynamically verify individual user addresses at send time. If individual address verification is in use, the admin must set `sender_mode = "static"`.

### "AWS SES Settings" DocType — new field

Add one field to the existing `aws_ses_settings.json` DocType definition:

| Field | Type | Label | Default | Options |
|-------|------|-------|---------|---------|
| `sender_mode` | Select | Sender Mode | `user_first` | `user_first\nstatic` |

**`user_first`** — Use the logged-in user's email as `From` when the user has a valid email on the configured SES-verified domain. Falls back to `default_sender_email` for system/scheduler sends (where `frappe.session.user == "Administrator"` or `"Guest"`).

**`static`** — Always use `default_sender_email`. Current behaviour. Safe for individual-address SES verification setups.

A description string on the field: _"user_first: From = logged-in user (requires SES domain verification). static: always use Default Sender Email."_

### Backend — `AwsSesRuntimeConfig` change

Add `sender_mode: str = "user_first"` to the frozen dataclass in `aws_ses_config.py`. Read it in `get_ses_runtime_config()`:

```python
sender_mode = cstr(doc.get("sender_mode") or "user_first").strip().lower()
if sender_mode not in {"user_first", "static"}:
    sender_mode = "user_first"
```

### Backend — `_apply_configured_sender()` change

The function currently always applies `config.default_sender_email`. Modify it to honour `sender_mode`:

```python
def _apply_configured_sender(message: bytes, config: AwsSesRuntimeConfig) -> bytes:
    payload = _ensure_bytes(message)
    static_sender_email = (config.default_sender_email or "").strip()
    static_sender_name  = (config.default_sender_name  or "").strip()

    # Resolve the effective From address
    if config.sender_mode == "user_first":
        effective_from = _resolve_user_sender(static_sender_email, static_sender_name)
    else:
        effective_from = None  # will use static path below

    if not effective_from:
        # static mode OR user_first fallback
        if not static_sender_email:
            return payload
        effective_from = formataddr((static_sender_name, static_sender_email)) \
            if static_sender_name else static_sender_email

    # ... (rest of current logic: parse, rewrite From, preserve original as Reply-To)
```

```python
def _resolve_user_sender(fallback_email: str, fallback_name: str) -> str | None:
    """Return 'Name <email>' for the current session user if eligible, else None."""
    user = getattr(frappe.session, "user", None)
    if not user or user in ("Administrator", "Guest", ""):
        return None
    try:
        from frappe.utils import get_formatted_email
        formatted = get_formatted_email(user)  # "Alice Smith <alice@tiberbu.app>"
        if not formatted:
            return None
        # Only use if the user's email is on the same domain as the SES fallback sender
        from email.utils import parseaddr
        _, user_email = parseaddr(formatted)
        _, fallback_email_addr = parseaddr(fallback_email)
        if not user_email or not fallback_email_addr:
            return None
        user_domain = user_email.split("@")[-1].lower()
        fallback_domain = fallback_email_addr.split("@")[-1].lower()
        if user_domain != fallback_domain:
            return None  # different domain → not safe to use as SES sender
        return formatted
    except Exception:
        return None
```

**Why domain-match check:** SES domain identity verification covers `*@domain`. If the user's email is `alice@tiberbu.app` and the verified domain is `tiberbu.app` (same domain as `default_sender_email`), the send is safe. If the user's email is a personal Gmail or a different corporate domain, SES will reject it.

**Reply-To behaviour in `user_first` mode:** When `effective_from` is the user's own address, the current "preserve original as Reply-To" logic should be skipped — the From IS the real person, and adding a redundant Reply-To to the same address is noise. The guard is: only set Reply-To if `original_from != effective_from`.

---

### SES-SENDER-1 — DocType + Python: `sender_mode` field + resolver (Backend)

**Files to change:**
- `frappe_devsecops_dashboard/frappe_devsecops_dashboard/doctype/aws_ses_settings/aws_ses_settings.json` — add `sender_mode` Select field
- `frappe_devsecops_dashboard/frappe_devsecops_dashboard/email/aws_ses_config.py` — add `sender_mode` to dataclass + `get_ses_runtime_config()`
- `frappe_devsecops_dashboard/frappe_devsecops_dashboard/email/aws_ses_override.py` — modify `_apply_configured_sender()`, add `_resolve_user_sender()`

**`bench migrate` required** after the DocType JSON change (adds the new column).

**Proof:**
1. Open "AWS SES Settings" in the Frappe desk. A "Sender Mode" select field is present with options "user_first" and "static".
2. Set `sender_mode = "user_first"`. Send a test email from a Lead while logged in as a real user (not Administrator). Inspect the delivered email headers — `From:` is `User Name <user@tiberbu.app>`, not the static sender.
3. Set `sender_mode = "static"`. Send again. `From:` is `default_sender_email`. No regression.
4. Log in as Administrator. Send with `sender_mode = "user_first"`. `From:` falls back to `default_sender_email` (Administrator has no valid user email on the domain).
5. Unit test: `_resolve_user_sender()` returns `None` for `Administrator`, `Guest`, empty user, and users with off-domain emails; returns formatted address for on-domain users.

---

### SES-SENDER-2 — Whitelisted API: `crm.api.ses` (Backend)

Create `crm/crm/api/ses.py`:

```python
import frappe
from frappe import _


@frappe.whitelist()
def get_settings():
    """Return public-safe SES settings for the frontend config UI.
    Secrets (access_key_id, secret_access_key, session_token) are never returned.
    """
    _require_manager()
    try:
        doc = frappe.get_cached_doc("AWS SES Settings", "AWS SES Settings")
    except frappe.DoesNotExistError:
        return {}
    return {
        "enabled": bool(doc.enabled),
        "aws_region": doc.aws_region or "",
        "default_sender_email": doc.default_sender_email or "",
        "default_sender_name": doc.default_sender_name or "",
        "sender_mode": doc.sender_mode or "user_first",
        "configuration_set_name": doc.configuration_set_name or "",
        "retry_mode": doc.retry_mode or "standard",
        "total_max_attempts": doc.total_max_attempts or 8,
        "use_explicit_credentials": bool(doc.use_explicit_credentials),
        "has_access_key": bool(doc.get_password("secret_access_key", raise_exception=False)),
    }


@frappe.whitelist(methods=["POST"])
def update_settings(settings: dict):
    """Save non-secret SES settings. Secrets are updated separately via Frappe desk."""
    _require_manager()
    ALLOWED = {
        "enabled", "aws_region", "default_sender_email", "default_sender_name",
        "sender_mode", "configuration_set_name", "retry_mode", "total_max_attempts",
        "use_explicit_credentials",
    }
    try:
        doc = frappe.get_doc("AWS SES Settings", "AWS SES Settings")
    except frappe.DoesNotExistError:
        frappe.throw(_("AWS SES Settings not found. Ensure frappe_devsecops_dashboard is installed."))

    for key, value in settings.items():
        if key in ALLOWED:
            doc.set(key, value)
    doc.save(ignore_permissions=True)
    frappe.clear_cache(doctype="AWS SES Settings")
    # invalidate per-request config cache on next call
    try:
        from frappe_devsecops_dashboard.email.aws_ses_config import clear_ses_runtime_config_cache
        clear_ses_runtime_config_cache()
    except ImportError:
        pass
    return get_settings()


def _require_manager():
    from crm.permissions import is_manager  # reuse existing CRM guard
    if not is_manager():
        frappe.throw(_("Only CRM Managers can modify SES settings."), frappe.PermissionError)
```

**Note:** `clear_ses_runtime_config_cache()` must be added to `aws_ses_config.py` in SES-SENDER-1. It already exists — it was defined in the original devsecops implementation.

**Proof:** `bench --site <site> execute crm.api.ses.get_settings` returns the expected JSON. Non-manager user receives a `PermissionError`. `update_settings({"enabled": True, "sender_mode": "static"})` persists and `get_settings()` reflects the change immediately.

---

### SES-UI-1 — `SESSettings.vue`: Settings UI page (Frontend)

**Location:** `frontend/src/components/Settings/SESSettings.vue`
**Added to Settings shell:** Under the `Email` tab group, new item `AWS SES` (below `Accounts`, above `Templates`), manager-only.

#### Layout (matches `GeneralSettings.vue` pattern)

```
SES Settings
Configure AWS Simple Email Service for outbound email delivery.

┌─ Enable SES ─────────────────────────────────────────────────────┐
│  Route all CRM outbound email through AWS SES instead of SMTP.   │
│                                              [Switch ●]           │
└───────────────────────────────────────────────────────────────────┘

[only shown when enabled=true]

┌─ AWS Configuration ───────────────────────────────────────────────┐
│  AWS Region          [eu-west-1          ▼]                       │
│  Configuration Set   [__________________]   (optional)            │
└───────────────────────────────────────────────────────────────────┘

┌─ Sender Identity ─────────────────────────────────────────────────┐
│  Sender Mode                                                       │
│  ● User first  — From: logged-in user (requires domain identity)  │
│  ○ Static      — From: always use Default Sender Email below      │
│                                                                    │
│  Default Sender Email   [crm@tiberbu.app      ]                   │
│  Default Sender Name    [Tiberbu CRM          ]                   │
│  (used when mode is "static" or user email is off-domain)         │
└───────────────────────────────────────────────────────────────────┘

┌─ Reliability ─────────────────────────────────────────────────────┐
│  Retry Mode     [standard  ▼]   (standard | adaptive | legacy)    │
│  Max Attempts   [8         ]                                       │
└───────────────────────────────────────────────────────────────────┘

┌─ Credentials ─────────────────────────────────────────────────────┐
│  Use Explicit Credentials                      [Switch ○]          │
│  When off, the EC2/ECS instance profile is used (recommended).    │
│  Secrets (Access Key / Secret) are managed in Frappe Desk →       │
│  AWS SES Settings. [Open in Desk ↗]                               │
└───────────────────────────────────────────────────────────────────┘

                              [Cancel]  [Save Changes ●]
```

#### Component spec

**State model:**
```typescript
interface SesSettingsForm {
  enabled: boolean
  aws_region: string
  configuration_set_name: string
  sender_mode: 'user_first' | 'static'
  default_sender_email: string
  default_sender_name: string
  retry_mode: 'standard' | 'adaptive' | 'legacy'
  total_max_attempts: number
  use_explicit_credentials: boolean
  has_access_key: boolean  // read-only, from API — shows "●●●●●● configured" badge
}
```

**Data fetching:** `createResource` on `get_settings`:
```js
const settings = createResource({
  url: 'crm.api.ses.get_settings',
  auto: true,
})
```

**Save:** POST to `update_settings` with the form state (secrets excluded — they're in Frappe desk).

**Dirty tracking:** `computed(() => JSON.stringify(form) !== JSON.stringify(original))` — show `Badge("Not Saved", theme="orange")` + enable Save button when dirty.

**Sender Mode:** Rendered as two radio buttons (`frappe-ui` does not have a RadioGroup; use `<FormControl type="select">` with options `["user_first", "static"]` OR implement two `<Button variant="outline">` toggle pills). The frappe-ui `Select`/`FormControl` approach is simpler and consistent with the rest of the Settings pages.

**Conditional visibility:**
- The entire AWS Configuration + Sender Identity + Reliability + Credentials sections are hidden (`v-if="form.enabled"`) when `enabled = false`. Rationale: no point configuring SES if it's disabled — reduces visual noise and prevents partially-saved invalid configs.
- The "Default Sender Email" and "Default Sender Name" fields are always shown when enabled (they serve as fallback even in `user_first` mode).

**"Open in Desk" link for secrets:** Direct link to the Frappe desk URL for the AWS SES Settings Single DocType:
```html
<a :href="`/app/aws-ses-settings`" target="_blank" class="text-ink-blue-6 underline">
  Open in Desk ↗
</a>
```
This avoids building a credential-entry form in the Vue SPA (password field security, masking complexity) by delegating secrets to the native Frappe desk form which already handles them.

**`has_access_key` display:** When `has_access_key = true` and `use_explicit_credentials = true`, show an inline indicator: `● Secret key configured` in `text-ink-gray-5`. When `false`, show `○ No secret key — using instance profile`.

#### Settings.vue wiring

In `Settings.vue`, add to the `Email` tab items array:

```js
{
  label: __('AWS SES'),
  icon: 'mail-check',  // or a custom CloudIcon
  component: markRaw(SESSettings),
  condition: () => isManager(),
},
```

Import `SESSettings` from `@/components/Settings/SESSettings.vue`.

**Proof:**
1. Open Settings → Email → AWS SES. The page loads with current values from `get_settings`.
2. Toggle "Enable SES" off — the configuration sections hide. Toggle on — they reappear.
3. Change "Sender Mode" to "static". Change "Default Sender Email". Click "Save Changes". A success toast appears.
4. Reload the Settings page (close + reopen). Changed values persist.
5. Non-manager user: the "AWS SES" item does not appear in the Settings nav.
6. Click "Open in Desk ↗" — the Frappe desk AWS SES Settings form opens in a new tab.
7. `pnpm build` passes zero warnings. `tsc --noEmit` clean.
8. Screenshot: Settings → Email → AWS SES in light mode and dark mode.

---

### Sender mode interaction with inbound threading (design note, not a new story)

When `sender_mode = "user_first"`:
- The `From` header on outbound emails is `alice@tiberbu.app`.
- Replies from the prospect arrive `To: alice@tiberbu.app`.
- The polled CRM inbox (`crm-inbox@tiberbu.app`) is the `Reply-To` only if the user's address and the CRM inbox differ.
- **Impact on SES-IN-1:** The IMAP polling mailbox must be `crm-inbox@tiberbu.app` (or whatever address receives replies). Replies addressed to `alice@tiberbu.app` will not reach the CRM inbox unless domain-level catch-all or a specific IMAP rule forwards them.
- **Recommended setup for user_first + inbound:** set an explicit `Reply-To: crm-inbox@tiberbu.app` on all outbound CRM emails (not on personal user sends). This is configurable via the existing `reply_to` param in `frappe.sendmail()`. A follow-on story can add a "CRM Reply-To Address" field to AWS SES Settings and wire it into `_apply_configured_sender()`.

This is a known limitation of the `user_first` mode — document in the UI with a help text: _"In user_first mode, ensure all CRM users have email addresses on the SES-verified domain. Replies will be addressed to the user directly unless a Reply-To is configured."_
