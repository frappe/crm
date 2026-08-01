# BMAD Epic Breakdown: SES Inbound Email — AWS Push Path

**Date:** 2026-08-01
**Project:** crm (Tiberbu CRM fork)
**Status:** Ready for sprint planning
**Branch:** careverse_fixes

---

## Architecture Summary

```
MX record (tiberbu.com) → AWS SES Receiving (eu-west-1)
  → Receipt Rule
      ├── Action 1: S3  — store raw MIME (48-hour lifecycle, large attachments)
      └── Action 2: SNS — push notification (inline content < 150KB, else S3 key ref)
          → SNS Topic → HTTPS subscription
              → POST /api/method/crm.api.ses_inbound.receive
                  → SNS sig verification
                  → content inline OR s3.get_object() for large emails
                  → parse raw MIME
                  → create Communication on Lead/Deal
                  → attach files as Frappe File records
```

**Key constraints:**
- SES email receiving is not available in eu-west-2. Inbound rule must be in eu-west-1.
- Outbound SES stays on eu-west-2. Inbound and outbound are independent.
- SNS delivers full email inline if < 150KB. For larger (attachments), the SNS payload
  contains `receipt.action.bucketName` + `receipt.action.objectKey` — fetch from S3.
- S3 lifecycle: delete after 48 hours (safety net for failed webhook deliveries).
  Attachments are downloaded and stored as Frappe Files on ingest — S3 is transit only.
- No Lambda, no polling, no IMAP account required.

---

## Requirements Inventory

### Functional Requirements

FR-1: AWS infrastructure (S3 bucket, SNS topic, receipt rule set + rule) must be
      provisionable via a single boto3 script run by an admin.

FR-2: SNS must deliver inbound email notifications to a CRM HTTPS webhook endpoint.

FR-3: CRM webhook must verify SNS message signatures before processing any payload.

FR-4: CRM webhook must handle the SNS subscription confirmation handshake automatically.

FR-5: CRM webhook must branch on payload size: use inline content if present, else
      fetch raw MIME from S3 using the bucket/key in the notification.

FR-6: Raw MIME must be parsed and threaded onto the correct Lead or Deal as a
      Communication doc, matched by In-Reply-To / References / sender email.

FR-7: Email attachments must be downloaded immediately and stored as Frappe File
      records linked to the Communication — not deferred to S3 fetch later.

FR-8: CRM SES Settings must expose inbound configuration fields:
      inbound_domain, inbound_region (eu-west-1), s3_bucket_name, sns_topic_arn.

FR-9: A whitelisted API must allow admins to trigger the AWS provisioning script
      from the CRM Settings UI.

### Non-Functional Requirements

NFR-1: The webhook endpoint must respond to SNS within 15 seconds to avoid redelivery.
       Heavy work (Communication create, file attach) must be enqueued, not inline.

NFR-2: SNS signature verification must use the certificate URL from the notification
       (fetched and cached) — never skip it in production.

NFR-3: No raw email body content in Frappe Error Log titles.

NFR-4: The provisioning script must be idempotent — safe to run multiple times.

NFR-5: S3 object lifecycle policy (48h delete) must be set by the provisioning script.

NFR-6: The solution must work regardless of whether the inbound domain is the same
       as the outbound sender domain.

---

## Epic 1: AWS Infrastructure Provisioning

One-shot boto3 script that creates and wires all required AWS resources.

---

### Story 1.1 — S3 bucket + 48h lifecycle policy

**Size:** S | **Turn budget:** 10

As a platform admin,
I want a boto3 provisioning script that creates the inbound S3 bucket with a 48-hour
object expiry lifecycle policy,
So that large inbound emails are stored transiently without manual cleanup.

**Acceptance Criteria**

Given the script runs against an AWS account with S3 permissions
When the bucket does not exist
Then the bucket is created in eu-west-1 with private ACL and versioning off.

Given the script runs again (idempotent)
When the bucket already exists
Then no error is raised and lifecycle policy is upserted.

Given the bucket exists after provisioning
When a lifecycle rule is applied
Then objects expire after exactly 2 days (ExpirationInDays: 2).

Given the bucket is created
When an SES receipt rule tries to write to it
Then the bucket policy grants `s3:PutObject` to `ses.amazonaws.com` principal
with `aws:Referer` condition scoped to the account.

**Files to create**
- `crm/email/ses_inbound_provision.py` (primary — provision function for S3)

**Depends on:** None
**Blocks:** Story 1.2, 1.3

---

### Story 1.2 — SNS topic + HTTPS subscription

**Size:** S | **Turn budget:** 10

As a platform admin,
I want the provisioning script to create an SNS topic and subscribe it to the CRM
webhook URL,
So that SES can push inbound notifications to CRM without polling.

**Acceptance Criteria**

Given the script runs with a valid `webhook_url` param
When the SNS topic does not exist
Then a Standard SNS topic named `careverse-crm-inbound` is created in eu-west-1.

Given the topic exists
When the HTTPS subscription does not exist
Then a `https` subscription is created pointing to `webhook_url`.

Given the subscription is created
When SNS sends a `SubscriptionConfirmation` notification to the webhook
Then the webhook auto-confirms by fetching `SubscribeURL` (handled in Story 2.1).

Given the script runs again (idempotent)
When the topic and subscription already exist
Then no duplicate topic or subscription is created.

**Files to modify**
- `crm/email/ses_inbound_provision.py` (extend with SNS section)

**Depends on:** Story 1.1 (same file)
**Blocks:** Story 1.3

---

### Story 1.3 — SES receipt rule set + receipt rule

**Size:** S | **Turn budget:** 10

As a platform admin,
I want the provisioning script to create an SES receipt rule in eu-west-1 with both
an S3 Action and an SNS Action,
So that every inbound email to the configured domain is stored and pushed to CRM.

**Acceptance Criteria**

Given the script runs with `recipient_domain` (e.g. `tiberbu.com`)
When the receipt rule set `careverse-crm-inbound` does not exist
Then it is created and activated (`set_active_receipt_rule_set`).

Given the rule set exists
When the receipt rule `crm-inbound` does not exist
Then a rule is created with:
- `Recipients: ["@<recipient_domain>"]` (catch-all for the domain)
- `Actions[0]`: S3Action to the bucket from Story 1.1
- `Actions[1]`: SNSAction to the topic from Story 1.2 with `Encoding: Base64`
- `TlsPolicy: Require`
- `ScanEnabled: True`

Given the script runs again (idempotent)
When the rule already exists
Then it is updated in-place (not duplicated).

Given provisioning completes
When an email is sent to any address at `recipient_domain`
Then SNS fires a notification within 30 seconds (verified manually post-deploy).

**Files to modify**
- `crm/email/ses_inbound_provision.py` (extend with SES section)

**Depends on:** Story 1.2
**Blocks:** Story 2.1

---

## Epic 2: CRM Webhook Handler

The Frappe-side endpoint that receives SNS notifications and creates Communications.

---

### Story 2.1 — SNS signature verification + subscription confirmation

**Size:** S | **Turn budget:** 10

As a security-conscious platform,
I want the webhook endpoint to verify every SNS notification signature and
auto-confirm subscriptions,
So that spoofed payloads are rejected and the subscription handshake is automated.

**Acceptance Criteria**

Given a POST arrives at `/api/method/crm.api.ses_inbound.receive`
When the `x-amz-sns-message-type` header is `SubscriptionConfirmation`
Then the handler fetches `SubscribeURL` from the payload and returns HTTP 200.

Given a POST arrives with `x-amz-sns-message-type: Notification`
When SNS signature verification passes
Then the handler returns HTTP 200 and enqueues processing.

Given a POST arrives with an invalid or missing signature
When verification fails
Then the handler returns HTTP 403 and logs the attempt.

Given the verification certificate URL
When it is fetched
Then it is cached in `frappe.cache()` for 24 hours (avoid per-request fetches).

**Files to create**
- `crm/api/ses_inbound.py` (primary — whitelist endpoint + SNS verification)

**Depends on:** Story 1.3 (SNS subscription exists to test against)
**Blocks:** Story 2.2

---

### Story 2.2 — Raw MIME fetch: inline vs S3 branch

**Size:** S | **Turn budget:** 10

As the inbound pipeline,
I want the email processing job to correctly obtain raw MIME bytes whether the
payload is inline or stored in S3,
So that both small replies and large attachment emails are handled uniformly.

**Acceptance Criteria**

Given an SNS notification where `Message.content` is present
When the job runs
Then raw MIME is taken from `Message.content` directly (no S3 call made).

Given an SNS notification where `Message.content` is absent
When the job runs
Then `receipt.action.bucketName` and `receipt.action.objectKey` are used to call
`s3.get_object()` with credentials from CRM SES Settings.

Given `s3.get_object()` is called
When the object does not exist (e.g. 48h expired)
Then an error is logged with the S3 key and the job exits cleanly (no crash).

Given raw MIME bytes are obtained either way
When passed to the parser
Then a standard Python `email.message.Message` object is returned.

**Files to modify**
- `crm/api/ses_inbound.py` (extend with fetch logic)

**Depends on:** Story 2.1
**Blocks:** Story 2.3

---

### Story 2.3 — Thread matching: route email to Lead or Deal

**Size:** M | **Turn budget:** 20

As a CRM user,
I want inbound replies threaded onto the correct Lead or Deal,
So that the full conversation is visible in one place without manual linking.

**Acceptance Criteria**

Given a parsed inbound email with an `In-Reply-To` or `References` header
When a Communication with a matching `message_id` exists in CRM
Then the inbound email is threaded as a reply on the same `reference_doctype`
and `reference_name` as that Communication.

Given no Communication matches by message-id
When the sender email matches a CRM Lead `email` field
Then the email is linked to that Lead.

Given no Communication and no Lead match
When `create_lead_from_incoming_email` is enabled in CRM SES Settings
Then a new CRM Lead is created with the sender's email and name from the From header.

Given no match and `create_lead_from_incoming_email` is disabled
Then the email is stored as an unlinked Communication with `reference_doctype` blank
and an Error Log entry is written.

**Files to modify**
- `crm/api/ses_inbound.py` (extend with thread matching + Communication creation)

**Depends on:** Story 2.2
**Blocks:** Story 2.4

---

### Story 2.4 — Attachment download and Frappe File storage

**Size:** M | **Turn budget:** 20

As a CRM agent,
I want email attachments (PDFs, images, tender documents) from inbound emails
stored as Frappe File records linked to the Communication,
So that I can open them directly from the Lead or Deal timeline without touching S3.

**Acceptance Criteria**

Given an inbound email with one or more MIME attachment parts
When the Communication is created
Then each attachment is saved as a `File` doc with `attached_to_doctype = Communication`
and `attached_to_name = <communication.name>`.

Given an attachment larger than 10MB
When stored as a Frappe File
Then it is stored using `frappe.get_doc("File").save()` without size truncation.

Given an attachment with a non-ASCII filename
When stored
Then the filename is sanitised (remove path separators, limit to 255 chars) but
not otherwise altered.

Given the Communication is created and files are attached
When the S3 object is still within the 48-hour window
Then the original S3 object is NOT deleted by CRM (lifecycle handles it).

**Files to modify**
- `crm/api/ses_inbound.py` (extend with attachment extraction + File creation)

**Depends on:** Story 2.3
**Blocks:** Story 3.1

---

## Epic 3: Settings UI + Admin Provisioning Trigger

Expose inbound config in CRM SES Settings and let admins trigger provisioning
from the UI.

---

### Story 3.1 — CRM SES Settings: inbound AWS fields

**Size:** S | **Turn budget:** 10

As a platform admin,
I want inbound AWS fields (inbound_region, s3_bucket_name, sns_topic_arn,
inbound_domain) stored on CRM SES Settings,
So that the webhook handler and provisioning script can read config from one place.

**Acceptance Criteria**

Given `bench migrate` has run
When the CRM SES Settings doctype is opened
Then four new fields are present: `inbound_region`, `s3_bucket_name`,
`sns_topic_arn`, `inbound_domain`.

Given the fields are saved
When `get_settings` API is called
Then all four fields are returned in the response.

Given `update_settings` is called with values for these fields
When the doc is saved
Then values are persisted and readable on next fetch.

**Files to modify**
- `crm/fcrm/doctype/crm_ses_settings/crm_ses_settings.json` (primary — add 4 fields)
- `crm/api/ses.py` (add 4 fields to `_SES_FIELDS`, `get_settings`, `update_settings`)

**Depends on:** Story 2.4
**Blocks:** Story 3.2

---

### Story 3.2 — SES Settings Vue: inbound AWS section + provision button

**Size:** M | **Turn budget:** 20

As a platform admin,
I want an "Inbound (AWS)" section in the SES Settings UI with the four AWS fields
and a "Provision AWS Infrastructure" button,
So that I can configure and trigger inbound setup without leaving CRM.

**Acceptance Criteria**

Given the SES Settings page loads
When `form.enabled` is true
Then an "Inbound (AWS)" section is visible with fields:
  Inbound Region (text, default `eu-west-1`),
  Inbound Domain (text, placeholder `tiberbu.com`),
  S3 Bucket Name (text),
  SNS Topic ARN (text, read-only after provisioning).

Given all required fields are filled
When the user clicks "Provision AWS Infrastructure"
Then a POST is made to `crm.api.ses_inbound.provision` with the field values.

Given provisioning succeeds
When the API returns
Then `sns_topic_arn` and `s3_bucket_name` are auto-filled from the response and
a success toast is shown.

Given provisioning fails
When the API returns an error
Then a red error message is shown inline (not a toast) with the AWS error detail.

**Files to modify**
- `frontend/src/components/Settings/SESSettings.vue` (primary — add inbound AWS section)

**Files to create**
- `crm/api/ses_inbound_provision_api.py` (whitelisted wrapper around
  `ses_inbound_provision.py` — returns `{sns_topic_arn, s3_bucket_name}`)

**Depends on:** Story 3.1
**Blocks:** None

---

## Story Execution Order

```
1.1 S3 bucket + lifecycle
  └─ 1.2 SNS topic + subscription
       └─ 1.3 SES receipt rule
            └─ 2.1 Webhook: SNS verification + subscription confirm
                 └─ 2.2 MIME fetch: inline vs S3
                      └─ 2.3 Thread matching → Communication
                           └─ 2.4 Attachment → Frappe File
                                └─ 3.1 DocType fields
                                     └─ 3.2 Vue UI + provision button
```

---

## Test Plan

| ID  | Test | Pass condition |
|-----|------|----------------|
| T1  | Provisioning is idempotent | Run script twice — no duplicate resources, no error |
| T2  | SNS subscription confirmation | Webhook auto-confirms; SNS shows subscription `Confirmed` |
| T3  | Signature rejection | POST with tampered signature → HTTP 403 in response + Error Log |
| T4  | Inline reply (< 150KB) | Send plain reply from Gmail → Communication created on Lead, no S3 fetch |
| T5  | Large attachment (> 150KB) | Send email with PDF attachment → S3 fetch path taken, File saved on Communication |
| T6  | Thread matching by message-id | Reply to a CRM-sent email → threaded on same Lead, not a new record |
| T7  | Thread matching by sender email | Fresh email from known Lead email → linked to Lead |
| T8  | Auto lead creation | Fresh email from unknown sender, `create_lead_from_incoming_email=1` → new Lead |
| T9  | 48h S3 expiry | Object older than 48h → `s3.get_object()` returns NoSuchKey → clean error log |
| T10 | Provision button in UI | Fill fields, click Provision → SNS ARN auto-fills, no manual AWS console visit |
