# Work Item — E1: AWS SES Inbound Provisioning
**Epic:** E1 — AWS Infrastructure Provisioning
**Feature:** SES Inbound Email — AWS Push Path
**Date:** 2026-08-01
**Status:** Ready for dev
**Branch:** careverse_fixes

Parent planning doc: `ses-inbound-epics-and-stories-2026-08-01.md`

---

## Context

All three stories in this epic write to the same file:
`crm/email/ses_inbound_provision.py`

Stories execute sequentially (1.1 → 1.2 → 1.3). Each story extends the file.
The finished file is a single callable entry-point:

```python
provision(
    aws_region_inbound="eu-west-1",    # SES receiving — NOT eu-west-2
    aws_region_outbound="eu-west-2",   # existing outbound region (for credentials)
    recipient_domain="tiberbu.com",
    s3_bucket_name="careverse-crm-inbound-email",
    sns_topic_name="careverse-crm-inbound",
    webhook_url="https://cr-dev.tiberbu.app/api/method/crm.api.ses_inbound.receive",
)
```

Returns:
```python
{
    "s3_bucket_name": "careverse-crm-inbound-email",
    "sns_topic_arn": "arn:aws:sns:eu-west-1:...:careverse-crm-inbound",
    "receipt_rule_set": "careverse-crm-inbound",
    "receipt_rule": "crm-inbound",
}
```

**Credentials:** Read from `CRM SES Settings` via `get_ses_runtime_config()` — same
boto3 session factory used by outbound. Do NOT hardcode keys.

**Idempotency contract:** Every create call must check existence first. Running
`provision()` twice must produce zero errors and zero duplicate resources.

---

## Story 1.1 — S3 Bucket + 48-hour Lifecycle Policy

**Size:** S | **Turn budget:** 10
**Primary file:** `crm/email/ses_inbound_provision.py` (create)

### What to build

A function `_provision_s3(s3_client, bucket_name, region)` that:

1. Creates the S3 bucket in `eu-west-1` (or skips if it already exists).
2. Blocks all public access (`PublicAccessBlockConfiguration` — all four flags True).
3. Puts a lifecycle configuration with one rule:
   - ID: `expire-inbound-email-48h`
   - Status: `Enabled`
   - Filter: prefix `""` (all objects)
   - `Expiration: {Days: 2}`
4. Puts a bucket policy granting SES permission to write objects:

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Sid": "AllowSESPuts",
    "Effect": "Allow",
    "Principal": {"Service": "ses.amazonaws.com"},
    "Action": "s3:PutObject",
    "Resource": "arn:aws:s3:::<bucket_name>/*",
    "Condition": {
      "StringEquals": {"aws:Referer": "<aws_account_id>"}
    }
  }]
}
```

`aws_account_id` must be resolved at runtime via `sts_client.get_caller_identity()["Account"]`.

### Acceptance Criteria

- [ ] Running `_provision_s3()` on a clean account → bucket created, no error.
- [ ] Running `_provision_s3()` again → no `BucketAlreadyOwnedByYou` or any error.
- [ ] `get_bucket_lifecycle_configuration()` shows `ExpirationInDays: 2`.
- [ ] `get_bucket_policy()` shows `AllowSESPuts` statement with correct ARN.
- [ ] `get_public_access_block()` shows all four flags as `True`.

### Files

```
## Files to create
- crm/email/ses_inbound_provision.py   ← start here
```

### Code skeleton

```python
from __future__ import annotations
import json
import logging
import frappe
from crm.email.ses_runtime import get_ses_runtime_config

_LOGGER = logging.getLogger(__name__)


def provision(
    aws_region_inbound: str,
    recipient_domain: str,
    s3_bucket_name: str,
    sns_topic_name: str,
    webhook_url: str,
) -> dict:
    config = get_ses_runtime_config()
    session = _get_boto3_session(config, aws_region_inbound)

    s3 = session.client("s3", region_name=aws_region_inbound)
    sts = session.client("sts")
    sns = session.client("sns", region_name=aws_region_inbound)
    ses = session.client("ses", region_name=aws_region_inbound)

    account_id = sts.get_caller_identity()["Account"]

    _provision_s3(s3, s3_bucket_name, aws_region_inbound, account_id)
    sns_topic_arn = _provision_sns(sns, sns_topic_name, webhook_url)
    _provision_ses_rules(ses, recipient_domain, s3_bucket_name, sns_topic_arn, account_id)

    return {
        "s3_bucket_name": s3_bucket_name,
        "sns_topic_arn": sns_topic_arn,
        "receipt_rule_set": "careverse-crm-inbound",
        "receipt_rule": "crm-inbound",
    }


def _get_boto3_session(config, region: str):
    import boto3
    kwargs = {"region_name": region}
    if config.use_explicit_credentials:
        kwargs["aws_access_key_id"] = config.access_key_id
        kwargs["aws_secret_access_key"] = config.secret_access_key
        if config.session_token:
            kwargs["aws_session_token"] = config.session_token
    return boto3.Session(**kwargs)


def _provision_s3(s3_client, bucket_name: str, region: str, account_id: str) -> None:
    # create bucket (idempotent)
    # block public access
    # put lifecycle (48h expiry)
    # put bucket policy (SES PutObject permission)
    pass  # implement in this story


def _provision_sns(sns_client, topic_name: str, webhook_url: str) -> str:
    # implement in story 1.2
    pass


def _provision_ses_rules(ses_client, recipient_domain: str, bucket_name: str,
                         sns_topic_arn: str, account_id: str) -> None:
    # implement in story 1.3
    pass
```

### Depends on
- None — first story in chain.

### Blocks
- Story 1.2 (extends the same file)

---

## Story 1.2 — SNS Topic + HTTPS Subscription

**Size:** S | **Turn budget:** 10
**Primary file:** `crm/email/ses_inbound_provision.py` (extend `_provision_sns`)

### What to build

Implement `_provision_sns(sns_client, topic_name, webhook_url) -> str`:

1. Check if topic exists: `list_topics()` — match by name suffix in ARN.
2. If not found: `create_topic(Name=topic_name)` → get ARN.
3. Check if HTTPS subscription to `webhook_url` already exists:
   `list_subscriptions_by_topic()` — match by `Protocol=https` and `Endpoint=webhook_url`.
4. If not found: `subscribe(TopicArn=arn, Protocol="https", Endpoint=webhook_url)`.
   - Set `Attributes={"RawMessageDelivery": "false"}` — CRM needs the SNS envelope
     (contains `x-amz-sns-message-type` and signature fields).
5. Return the topic ARN.

Note: SNS subscription starts as `PendingConfirmation`. It becomes `Confirmed` when
the CRM webhook (Story 2.1) handles the `SubscriptionConfirmation` notification.

### Acceptance Criteria

- [ ] `list_topics()` shows `careverse-crm-inbound` after first run.
- [ ] `list_subscriptions_by_topic()` shows one `https` subscription to `webhook_url`.
- [ ] Running `_provision_sns()` again → no duplicate topic, no duplicate subscription.
- [ ] Return value is a valid SNS ARN string (`arn:aws:sns:eu-west-1:...`).

### Files

```
## Files to modify
- crm/email/ses_inbound_provision.py   ← implement _provision_sns
```

### Depends on
- Story 1.1 (file exists, `provision()` scaffold in place)

### Blocks
- Story 1.3

---

## Story 1.3 — SES Receipt Rule Set + Receipt Rule

**Size:** S | **Turn budget:** 10
**Primary file:** `crm/email/ses_inbound_provision.py` (extend `_provision_ses_rules`)

### What to build

Implement `_provision_ses_rules(ses_client, recipient_domain, bucket_name, sns_topic_arn, account_id)`:

1. **Rule set** — check if `careverse-crm-inbound` exists via `list_receipt_rule_sets()`.
   If not: `create_receipt_rule_set(RuleSetName="careverse-crm-inbound")`.
   Always call `set_active_receipt_rule_set(RuleSetName="careverse-crm-inbound")`.

2. **Receipt rule** — check if rule `crm-inbound` exists via
   `describe_receipt_rule_set(RuleSetName=...)["Rules"]` — match by `Name`.

   If not found → `create_receipt_rule(...)`.
   If found → `update_receipt_rule(...)`.

   Rule definition:
   ```python
   Rule = {
       "Name": "crm-inbound",
       "Enabled": True,
       "TlsPolicy": "Require",
       "ScanEnabled": True,
       "Recipients": [recipient_domain],   # catches all @tiberbu.com
       "Actions": [
           {
               "S3Action": {
                   "BucketName": bucket_name,
                   "ObjectKeyPrefix": "inbound/",
                   # no TopicArn here — SNS notification comes from Action 2
               }
           },
           {
               "SNSAction": {
                   "TopicArn": sns_topic_arn,
                   "Encoding": "Base64",   # raw MIME bytes safe in JSON
               }
           },
       ],
   }
   ```

3. **MX record reminder** — after provisioning, log a WARNING:
   ```
   ACTION REQUIRED: Add MX record for <recipient_domain>:
     10 inbound-smtp.eu-west-1.amazonaws.com
   Without this record, SES will not receive email for this domain.
   ```

### Acceptance Criteria

- [ ] `list_receipt_rule_sets()` shows `careverse-crm-inbound` after first run.
- [ ] `describe_receipt_rule_set()` shows rule `crm-inbound` with S3Action + SNSAction.
- [ ] Rule `Recipients` contains `tiberbu.com` (or whatever `recipient_domain` was passed).
- [ ] Running `_provision_ses_rules()` again → no error, rule is updated not duplicated.
- [ ] The WARNING about MX record appears in the Frappe log after provisioning.
- [ ] `provision()` returns dict with all four keys populated.

### Final `provision()` call verification

After all three stories are done, run from bench console:

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

### Files

```
## Files to modify
- crm/email/ses_inbound_provision.py   ← implement _provision_ses_rules + MX warning
```

### Depends on
- Story 1.2

### Blocks
- Story 2.1 (webhook handler — needs SNS subscription to confirm against)

---

## E1 Definition of Done

- [ ] `ses_inbound_provision.py` exists and imports cleanly.
- [ ] `provision()` runs end-to-end without error on a clean AWS account.
- [ ] `provision()` runs again with zero errors (full idempotency).
- [ ] S3 bucket: private, 48h lifecycle, SES bucket policy.
- [ ] SNS topic: exists, HTTPS subscription pending confirmation.
- [ ] SES rule set: active, rule has S3Action + SNSAction, TLS required.
- [ ] MX record WARNING logged.
- [ ] No AWS credentials appear in any log line.
