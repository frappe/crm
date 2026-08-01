# DevOps Work Instruction — SES Inbound Email: AWS Provisioning
**Date:** 2026-08-01
**Owner:** DevOps / Platform Engineer
**Environment:** AWS Console + DNS provider
**Estimated time:** 30–45 minutes

---

## Overview

This instruction provisions the AWS infrastructure required for Tiberbu CRM to receive
inbound email without an IMAP mailbox. When complete, any email sent to `@tiberbu.com`
will be delivered to the CRM via SNS HTTP push — no polling, no mail server.

```
Sender (Gmail / Yahoo / Roundcube / any)
  → DNS MX lookup for tiberbu.com
  → AWS SES receiving endpoint (eu-west-1)
  → Receipt Rule
      ├── S3 bucket  (raw MIME stored for 48h — large attachments)
      └── SNS topic  (HTTP POST to CRM webhook)
          → CRM processes email → Communication doc created
```

> **Important:** AWS SES email *receiving* is only available in `us-east-1`,
> `us-west-2`, and `eu-west-1`. Your outbound SES runs on `eu-west-2` — that
> is unchanged. Inbound uses `eu-west-1` only.

---

## Prerequisites

Before starting, confirm you have:

- [ ] AWS Console access with IAM permissions for: SES, S3, SNS, STS
- [ ] Access to the DNS zone for `tiberbu.com` (Route 53 or external registrar)
- [ ] The CRM production URL: `https://cr-dev.tiberbu.app` (update for prod)
- [ ] SES domain `tiberbu.com` already verified for **sending** in `eu-west-2`
  (this instruction adds receiving in `eu-west-1` — separate verification needed)

---

## Step 1 — Verify tiberbu.com domain in SES eu-west-1

SES receiving requires the domain to be verified in **eu-west-1** independently
of eu-west-2 outbound verification.

1. Open AWS Console → switch region to **eu-west-1**
2. Navigate to **Amazon SES → Configuration → Verified identities**
3. Click **Create identity** → choose **Domain** → enter `tiberbu.com`
4. AWS will provide a DKIM CNAME record set (3 records). Add them to your DNS zone.
5. Wait for status to show **Verified** (usually 5–15 minutes after DNS propagates).

> If `tiberbu.com` already shows Verified in eu-west-1, skip to Step 2.

---

## Step 2 — Run the CRM provisioning script

The CRM codebase includes an idempotent script that creates the S3 bucket, SNS topic,
and SES receipt rule in one command. Run it from the bench server:

```bash
cd /home/ubuntu/frappe-bench
bench --site cr-dev.tiberbu.app console
```

Then paste and run:

```python
from crm.email.ses_inbound_provision import provision

result = provision(
    aws_region_inbound="eu-west-1",
    recipient_domain="tiberbu.com",
    s3_bucket_name="careverse-crm-inbound-email",
    sns_topic_name="careverse-crm-inbound",
    webhook_url="https://cr-dev.tiberbu.app/api/method/crm.api.ses_inbound.receive",
)
print(result)
```

Expected output:
```python
{
    "s3_bucket_name": "careverse-crm-inbound-email",
    "sns_topic_arn": "arn:aws:sns:eu-west-1:<account_id>:careverse-crm-inbound",
    "receipt_rule_set": "careverse-crm-inbound",
    "receipt_rule": "crm-inbound",
}
```

Note the `sns_topic_arn` — you will need it in Step 5.

**If the script errors:** Check Frappe Error Log at
`/app/error-log` and share the `CRM SES Settings` screenshot with the dev team.
The script uses the same AWS credentials stored in CRM SES Settings (outbound).
Ensure those credentials have the IAM permissions listed in the Appendix.

---

## Step 3 — Add the MX record

This is the single DNS change that routes inbound email to AWS SES.

| Type | Name | Priority | Value |
|------|------|----------|-------|
| MX | `tiberbu.com` | `10` | `inbound-smtp.eu-west-1.amazonaws.com` |

**In Route 53:**
1. Open Route 53 → Hosted zones → `tiberbu.com`
2. Click **Create record**
3. Record type: `MX`
4. Value: `10 inbound-smtp.eu-west-1.amazonaws.com`
5. TTL: `300` (5 minutes — lower TTL during testing)
6. Click **Create records**

**In an external registrar (GoDaddy, Cloudflare, etc.):**
Add an MX record with host `@`, priority `10`,
value `inbound-smtp.eu-west-1.amazonaws.com`.

> DNS propagation takes 5–30 minutes. Use `dig MX tiberbu.com` to confirm
> the record is live before testing.

---

## Step 4 — Confirm the SNS subscription

After the provisioning script runs, the SNS subscription is in
`PendingConfirmation` state. The CRM webhook auto-confirms it when SNS
sends the first HTTP request — but only after the subscription is created.

**Verify confirmation:**

1. Open AWS Console → **Amazon SNS → eu-west-1 → Topics**
2. Find `careverse-crm-inbound`
3. Click the topic → scroll to **Subscriptions**
4. The subscription to the CRM webhook URL should show status **Confirmed**

If it still shows `PendingConfirmation` after 2 minutes:
- Check the CRM webhook is publicly reachable:
  ```
  curl -s -o /dev/null -w "%{http_code}" https://cr-dev.tiberbu.app/api/method/crm.api.ses_inbound.receive
  ```
  Should return `405` (Method Not Allowed for GET) — confirms the endpoint exists.
- Check Frappe Error Log for any SNS confirmation errors.
- In the SNS console, click **Request confirmation** to re-trigger.

---

## Step 5 — Save SNS details in CRM SES Settings

1. Open CRM → Settings → AWS SES
2. Scroll to the **Inbound (AWS)** section
3. Fill in:
   - **Inbound Region:** `eu-west-1`
   - **Inbound Domain:** `tiberbu.com`
   - **S3 Bucket Name:** `careverse-crm-inbound-email`
   - **SNS Topic ARN:** *(paste from Step 2 output)*
4. Click **Save Changes**

---

## Step 6 — Send a test email

Send a test email from any external mailbox (Gmail, Yahoo, etc.) to any address
at `tiberbu.com`, e.g. `test-inbound@tiberbu.com`.

**Verify the result:**

```bash
bench --site cr-dev.tiberbu.app console
```

```python
import frappe
# Check the Email Queue is not stuck
rows = frappe.db.sql(
    "SELECT name, status FROM `tabEmail Queue` ORDER BY creation DESC LIMIT 3",
    as_dict=True
)
print(rows)

# Check a Communication was created
comms = frappe.get_list(
    "Communication",
    filters={"sent_or_received": "Received"},
    fields=["name", "subject", "sender", "reference_doctype", "reference_name"],
    order_by="creation desc",
    limit=3,
)
print(comms)
```

Expected: a `Communication` doc with `sent_or_received = Received` and the
sender's email in the `sender` field.

---

## Step 7 — Verify SES sandbox limits (production only)

By default, AWS SES accounts start in sandbox mode and can only send/receive
from verified addresses. For production:

1. Open AWS Console → **Amazon SES → Account dashboard**
2. Under **Sending limits**, check if you are in sandbox
3. If in sandbox: click **Request production access** and complete the form
4. AWS typically approves within 24h

> SES **receiving** works even in sandbox — emails from any sender are accepted.
> Sandbox only restricts *outbound* sending to unverified addresses.

---

## Rollback

To remove all inbound infrastructure:

1. **SES:** Console → SES eu-west-1 → Email receiving → Rule sets →
   Select `careverse-crm-inbound` → Set as inactive → Delete
2. **SNS:** Console → SNS eu-west-1 → Topics → Delete `careverse-crm-inbound`
3. **S3:** Console → S3 → Empty bucket `careverse-crm-inbound-email` → Delete bucket
4. **DNS:** Remove the MX record for `tiberbu.com`

---

## Appendix — Required IAM Permissions

The AWS credentials stored in CRM SES Settings need the following policy
for provisioning (can be removed after provisioning is complete):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "SESInboundProvision",
      "Effect": "Allow",
      "Action": [
        "s3:CreateBucket",
        "s3:PutBucketPublicAccessBlock",
        "s3:PutLifecycleConfiguration",
        "s3:PutBucketPolicy",
        "sns:ListTopics",
        "sns:CreateTopic",
        "sns:ListSubscriptionsByTopic",
        "sns:Subscribe",
        "ses:ListReceiptRuleSets",
        "ses:CreateReceiptRuleSet",
        "ses:SetActiveReceiptRuleSet",
        "ses:DescribeReceiptRuleSet",
        "ses:CreateReceiptRule",
        "ses:UpdateReceiptRule",
        "sts:GetCallerIdentity"
      ],
      "Resource": "*"
    }
  ]
}
```

For **runtime** (webhook processing only, after provisioning):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "SESInboundRuntime",
      "Effect": "Allow",
      "Action": [
        "s3:GetObject"
      ],
      "Resource": "arn:aws:s3:::careverse-crm-inbound-email/*"
    }
  ]
}
```

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| MX record not resolving | DNS not propagated | Wait 15 min, retry `dig MX tiberbu.com` |
| SNS subscription stuck in PendingConfirmation | CRM URL not reachable from public internet | Check nginx config, open firewall port 443 |
| Communication not created after test email | SNS not delivering | Check SNS delivery status in console; check Frappe Error Log |
| `NoSuchKey` in Frappe Error Log | Email arrived, S3 stored, but 48h window elapsed before processing | Redelivery not possible — resend the test email |
| Signature verification rejected | Clock skew > 15 min on server | Run `ntpdate -u pool.ntp.org` or sync server time |
| `MessageRejected` from SES (outbound) | Sender domain not verified for eu-west-1 | Complete Step 1 domain verification |
