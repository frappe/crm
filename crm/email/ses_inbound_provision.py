from __future__ import annotations

import json
import logging

import frappe

from crm.email.ses_runtime import get_ses_runtime_config

_LOGGER = logging.getLogger(__name__)

_RULE_SET = "careverse-crm-inbound"
_RULE_NAME = "crm-inbound"
_S3_PREFIX = "inbound/"


def provision(
    aws_region_inbound: str,
    recipient_domain: str,
    s3_bucket_name: str,
    sns_topic_name: str,
    webhook_url: str,
) -> dict:
    """Idempotent: creates S3 bucket, SNS topic, and SES receipt rules for inbound email.

    Safe to run multiple times — existing resources are updated, never duplicated.
    Returns the ARNs and names needed by the CRM webhook configuration.
    """
    config = get_ses_runtime_config()
    session = _get_boto3_session(config, aws_region_inbound)

    s3 = session.client("s3", region_name=aws_region_inbound)
    sts = session.client("sts")
    sns = session.client("sns", region_name=aws_region_inbound)
    ses = session.client("ses", region_name=aws_region_inbound)

    account_id = sts.get_caller_identity()["Account"]

    _provision_s3(s3, s3_bucket_name, aws_region_inbound, account_id)
    sns_topic_arn = _provision_sns(sns, sns_topic_name, webhook_url)
    _provision_ses_rules(ses, recipient_domain, s3_bucket_name, sns_topic_arn)

    return {
        "s3_bucket_name": s3_bucket_name,
        "sns_topic_arn": sns_topic_arn,
        "receipt_rule_set": _RULE_SET,
        "receipt_rule": _RULE_NAME,
    }


# ---------------------------------------------------------------------------
# S3
# ---------------------------------------------------------------------------

def _provision_s3(s3_client, bucket_name: str, region: str, account_id: str) -> None:
    _s3_create_bucket(s3_client, bucket_name, region)
    _s3_block_public_access(s3_client, bucket_name)
    _s3_put_lifecycle(s3_client, bucket_name)
    _s3_put_bucket_policy(s3_client, bucket_name, account_id)
    _LOGGER.info("S3 bucket provisioned: %s", bucket_name)


def _s3_create_bucket(s3_client, bucket_name: str, region: str) -> None:
    from botocore.exceptions import ClientError
    try:
        if region == "us-east-1":
            s3_client.create_bucket(Bucket=bucket_name)
        else:
            s3_client.create_bucket(
                Bucket=bucket_name,
                CreateBucketConfiguration={"LocationConstraint": region},
            )
        _LOGGER.info("Created S3 bucket: %s", bucket_name)
    except ClientError as exc:
        code = exc.response["Error"]["Code"]
        if code in ("BucketAlreadyOwnedByYou", "BucketAlreadyExists"):
            _LOGGER.info("S3 bucket already exists: %s", bucket_name)
        else:
            raise


def _s3_block_public_access(s3_client, bucket_name: str) -> None:
    s3_client.put_public_access_block(
        Bucket=bucket_name,
        PublicAccessBlockConfiguration={
            "BlockPublicAcls": True,
            "IgnorePublicAcls": True,
            "BlockPublicPolicy": True,
            "RestrictPublicBuckets": True,
        },
    )


def _s3_put_lifecycle(s3_client, bucket_name: str) -> None:
    s3_client.put_bucket_lifecycle_configuration(
        Bucket=bucket_name,
        LifecycleConfiguration={
            "Rules": [
                {
                    "ID": "expire-inbound-email-48h",
                    "Status": "Enabled",
                    "Filter": {"Prefix": ""},
                    "Expiration": {"Days": 2},
                }
            ]
        },
    )


def _s3_put_bucket_policy(s3_client, bucket_name: str, account_id: str) -> None:
    policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "AllowSESPuts",
                "Effect": "Allow",
                "Principal": {"Service": "ses.amazonaws.com"},
                "Action": "s3:PutObject",
                "Resource": "arn:aws:s3:::" + bucket_name + "/*",
                "Condition": {
                    "StringEquals": {"aws:Referer": account_id}
                },
            }
        ],
    }
    s3_client.put_bucket_policy(Bucket=bucket_name, Policy=json.dumps(policy))


# ---------------------------------------------------------------------------
# SNS
# ---------------------------------------------------------------------------

def _provision_sns(sns_client, topic_name: str, webhook_url: str) -> str:
    topic_arn = _sns_get_or_create_topic(sns_client, topic_name)
    _sns_ensure_subscription(sns_client, topic_arn, webhook_url)
    _LOGGER.info("SNS topic provisioned: %s", topic_arn)
    return topic_arn


def _sns_get_or_create_topic(sns_client, topic_name: str) -> str:
    paginator = sns_client.get_paginator("list_topics")
    for page in paginator.paginate():
        for topic in page.get("Topics", []):
            arn = topic["TopicArn"]
            if arn.split(":")[-1] == topic_name:
                _LOGGER.info("SNS topic already exists: %s", arn)
                return arn

    response = sns_client.create_topic(Name=topic_name)
    arn = response["TopicArn"]
    _LOGGER.info("Created SNS topic: %s", arn)
    return arn


def _sns_ensure_subscription(sns_client, topic_arn: str, webhook_url: str) -> None:
    paginator = sns_client.get_paginator("list_subscriptions_by_topic")
    for page in paginator.paginate(TopicArn=topic_arn):
        for sub in page.get("Subscriptions", []):
            if sub.get("Protocol") == "https" and sub.get("Endpoint") == webhook_url:
                _LOGGER.info("SNS subscription already exists for %s", webhook_url)
                return

    sns_client.subscribe(
        TopicArn=topic_arn,
        Protocol="https",
        Endpoint=webhook_url,
        Attributes={"RawMessageDelivery": "false"},
    )
    _LOGGER.info("SNS subscription created (PendingConfirmation) for %s", webhook_url)


# ---------------------------------------------------------------------------
# SES receipt rules
# ---------------------------------------------------------------------------

def _provision_ses_rules(
    ses_client,
    recipient_domain: str,
    bucket_name: str,
    sns_topic_arn: str,
) -> None:
    _ses_ensure_rule_set(ses_client)
    _ses_upsert_rule(ses_client, recipient_domain, bucket_name, sns_topic_arn)
    _LOGGER.warning(
        "ACTION REQUIRED: Add MX record for %s — "
        "10 inbound-smtp.eu-west-1.amazonaws.com — "
        "Without this record SES will not receive email for this domain.",
        recipient_domain,
    )


def _ses_ensure_rule_set(ses_client) -> None:
    existing = [
        rs["Name"]
        for rs in ses_client.list_receipt_rule_sets().get("RuleSets", [])
    ]
    if _RULE_SET not in existing:
        ses_client.create_receipt_rule_set(RuleSetName=_RULE_SET)
        _LOGGER.info("Created SES receipt rule set: %s", _RULE_SET)
    else:
        _LOGGER.info("SES receipt rule set already exists: %s", _RULE_SET)

    ses_client.set_active_receipt_rule_set(RuleSetName=_RULE_SET)


def _ses_upsert_rule(
    ses_client,
    recipient_domain: str,
    bucket_name: str,
    sns_topic_arn: str,
) -> None:
    rule_def = {
        "Name": _RULE_NAME,
        "Enabled": True,
        "TlsPolicy": "Require",
        "ScanEnabled": True,
        "Recipients": [recipient_domain],
        "Actions": [
            {
                "S3Action": {
                    "BucketName": bucket_name,
                    "ObjectKeyPrefix": _S3_PREFIX,
                }
            },
            {
                "SNSAction": {
                    "TopicArn": sns_topic_arn,
                    "Encoding": "Base64",
                }
            },
        ],
    }

    existing_rules = ses_client.describe_receipt_rule_set(
        RuleSetName=_RULE_SET
    ).get("Rules", [])
    existing_names = [r["Name"] for r in existing_rules]

    if _RULE_NAME in existing_names:
        ses_client.update_receipt_rule(RuleSetName=_RULE_SET, Rule=rule_def)
        _LOGGER.info("Updated SES receipt rule: %s", _RULE_NAME)
    else:
        ses_client.create_receipt_rule(RuleSetName=_RULE_SET, Rule=rule_def)
        _LOGGER.info("Created SES receipt rule: %s", _RULE_NAME)


# ---------------------------------------------------------------------------
# boto3 session
# ---------------------------------------------------------------------------

def _get_boto3_session(config, region: str):
    import boto3
    kwargs: dict = {"region_name": region}
    if config.use_explicit_credentials:
        kwargs["aws_access_key_id"] = config.access_key_id
        kwargs["aws_secret_access_key"] = config.secret_access_key
        if config.session_token:
            kwargs["aws_session_token"] = config.session_token
    return boto3.Session(**kwargs)
