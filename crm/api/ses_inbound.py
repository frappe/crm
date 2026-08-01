"""SES inbound email webhook handler.

Endpoint: POST /api/method/crm.api.ses_inbound.receive

Flow:
  1. SNS sends HTTP POST with JSON envelope.
  2. Handler verifies SNS signature (rejects spoofed payloads).
  3. SubscriptionConfirmation  → auto-confirm by fetching SubscribeURL.
  4. Notification              → enqueue _process_inbound_notification (async).
  5. Worker picks up job       → fetch raw MIME (inline or S3) → parse →
     thread-match Lead/Deal → create Communication → save attachments as Files.
"""
from __future__ import annotations

import base64
import hashlib
import json
import logging
import re
from email import message_from_bytes
from email.header import decode_header
from email.utils import parseaddr

import frappe
from frappe import _

_LOGGER = logging.getLogger(__name__)

# SNS signature algorithm
_SNS_SIGN_ALGO = "SHA256withRSA"
# Cache cert for 24h (86400s) to avoid per-request fetches
_CERT_CACHE_TTL = 86400
# Certificate URL must come from AWS SNS domains only
_CERT_URL_PATTERN = re.compile(
    r"^https://sns\.[a-z0-9-]+\.amazonaws\.com/",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Public endpoint — Story 2.1
# ---------------------------------------------------------------------------

@frappe.whitelist(allow_guest=True, methods=["POST"])
def receive():
    """SNS webhook entry point. Must respond quickly — heavy work is enqueued."""
    try:
        raw_body = frappe.request.get_data()
        payload = json.loads(raw_body)
    except Exception as exc:
        _LOGGER.warning("SES inbound: failed to parse SNS payload: %s", exc)
        frappe.response["http_status_code"] = 400
        return

    msg_type = frappe.request.headers.get("x-amz-sns-message-type", "")

    if msg_type == "SubscriptionConfirmation":
        _handle_subscription_confirmation(payload)
        return

    if msg_type == "Notification":
        if not _verify_sns_signature(payload, raw_body):
            frappe.response["http_status_code"] = 403
            frappe.log_error(
                title="SES Inbound: SNS Signature Rejected",
                message="TopicArn=%s MessageId=%s" % (payload.get("TopicArn"), payload.get("MessageId")),
            )
            return
        _enqueue_notification(payload)
        return

    # UnsubscribeConfirmation or unknown — ignore silently
    frappe.response["http_status_code"] = 200


def _handle_subscription_confirmation(payload: dict) -> None:
    subscribe_url = payload.get("SubscribeURL")
    if not subscribe_url:
        return
    try:
        import requests as _requests
        resp = _requests.get(subscribe_url, timeout=10)
        resp.raise_for_status()
        _LOGGER.info("SES inbound: SNS subscription confirmed for %s", payload.get("TopicArn"))
    except Exception as exc:
        frappe.log_error(
            title="SES Inbound: Subscription Confirmation Failed",
            message=str(exc),
        )


def _enqueue_notification(payload: dict) -> None:
    frappe.enqueue(
        "crm.api.ses_inbound._process_inbound_notification",
        queue="short",
        now=frappe.in_test,
        payload=payload,
    )


# ---------------------------------------------------------------------------
# SNS signature verification — Story 2.1
# ---------------------------------------------------------------------------

def _verify_sns_signature(payload: dict, raw_body: bytes) -> bool:
    """Verify SNS message signature using the certificate from AWS."""
    try:
        cert_url = payload.get("SigningCertURL", "")
        if not _CERT_URL_PATTERN.match(cert_url):
            _LOGGER.warning("SES inbound: cert URL domain not trusted: %s", cert_url)
            return False

        signature_b64 = payload.get("Signature", "")
        if not signature_b64:
            return False

        cert_pem = _get_cached_cert(cert_url)
        if not cert_pem:
            return False

        message_to_sign = _build_sign_string(payload)
        signature_bytes = base64.b64decode(signature_b64)

        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import padding
        from cryptography.x509 import load_pem_x509_certificate

        cert = load_pem_x509_certificate(cert_pem.encode())
        public_key = cert.public_key()
        public_key.verify(
            signature_bytes,
            message_to_sign.encode("utf-8"),
            padding.PKCS1v15(),
            hashes.SHA256(),
        )
        return True
    except Exception as exc:
        _LOGGER.warning("SES inbound: signature verification failed: %s", exc)
        return False


def _build_sign_string(payload: dict) -> str:
    """Build the canonical string SNS signs, per AWS documentation."""
    msg_type = payload.get("Type", "")
    if msg_type == "Notification":
        keys = ["Message", "MessageId", "Subject", "Timestamp", "TopicArn", "Type"]
    else:
        keys = ["Message", "MessageId", "SubscribeURL", "Timestamp", "Token", "TopicArn", "Type"]

    parts = []
    for key in keys:
        if key in payload:
            parts.append(key)
            parts.append(payload[key])
    return "\n".join(parts) + "\n"


def _get_cached_cert(cert_url: str) -> str | None:
    cache_key = "sns_cert_" + hashlib.md5(cert_url.encode()).hexdigest()
    cached = frappe.cache().get_value(cache_key)
    if cached:
        return cached
    try:
        import requests as _requests
        resp = _requests.get(cert_url, timeout=10)
        resp.raise_for_status()
        pem = resp.text
        frappe.cache().set_value(cache_key, pem, expires_in_sec=_CERT_CACHE_TTL)
        return pem
    except Exception as exc:
        _LOGGER.warning("SES inbound: failed to fetch SNS cert from %s: %s", cert_url, exc)
        return None


# ---------------------------------------------------------------------------
# Background job — Stories 2.2, 2.3, 2.4
# ---------------------------------------------------------------------------

def _process_inbound_notification(payload: dict) -> None:
    """Background job: fetch MIME → parse → thread → attach files."""
    try:
        raw_mime = _fetch_raw_mime(payload)
        if not raw_mime:
            return
        msg = message_from_bytes(raw_mime)
        _create_inbound_communication(msg)
    except Exception:
        frappe.log_error(
            title="SES Inbound: Processing Failed",
            message=frappe.get_traceback(),
        )


# ---------------------------------------------------------------------------
# Story 2.2 — Inline vs S3 MIME fetch
# ---------------------------------------------------------------------------

def _fetch_raw_mime(payload: dict) -> bytes | None:
    """Return raw MIME bytes from SNS inline content or S3 fallback."""
    try:
        message_obj = json.loads(payload.get("Message", "{}"))
    except Exception:
        _LOGGER.warning("SES inbound: could not parse SNS Message field")
        return None

    # Inline path: full email in 'content' field (< ~150KB)
    content = message_obj.get("content")
    if content:
        return content.encode("utf-8") if isinstance(content, str) else content

    # S3 path: large email stored by receipt rule S3Action
    action = (message_obj.get("receipt") or {}).get("action") or {}
    bucket = action.get("bucketName")
    key = action.get("objectKey")

    if not bucket or not key:
        frappe.log_error(
            title="SES Inbound: No Content and No S3 Key",
            message="MessageId=%s receipt=%s" % (payload.get("MessageId"), message_obj.get("receipt")),
        )
        return None

    return _fetch_from_s3(bucket, key)


def _fetch_from_s3(bucket: str, key: str) -> bytes | None:
    from crm.email.ses_runtime import get_ses_runtime_config
    from crm.email.ses_inbound_provision import _get_boto3_session

    config = get_ses_runtime_config()
    inbound_region = frappe.db.get_single_value("CRM SES Settings", "inbound_region") or "eu-west-1"
    session = _get_boto3_session(config, inbound_region)
    s3 = session.client("s3", region_name=inbound_region)

    try:
        response = s3.get_object(Bucket=bucket, Key=key)
        return response["Body"].read()
    except s3.exceptions.NoSuchKey:
        frappe.log_error(
            title="SES Inbound: S3 Object Expired or Missing",
            message="bucket=%s key=%s — 48h window may have elapsed" % (bucket, key),
        )
        return None
    except Exception as exc:
        frappe.log_error(
            title="SES Inbound: S3 Fetch Failed",
            message="bucket=%s key=%s error=%s" % (bucket, key, exc),
        )
        return None


# ---------------------------------------------------------------------------
# Story 2.3 — Thread matching + Communication creation
# ---------------------------------------------------------------------------

def _create_inbound_communication(msg) -> None:
    """Parse email message, find/create the linked record, save Communication."""
    from_header = msg.get("From", "")
    _, sender_email = parseaddr(from_header)
    sender_email = (sender_email or "").lower().strip()

    subject = _decode_mime_words(msg.get("Subject", "(no subject)"))
    message_id = (msg.get("Message-ID") or "").strip()
    in_reply_to = (msg.get("In-Reply-To") or "").strip()
    references = (msg.get("References") or "").strip()

    # Extract body
    body_html, body_text = _extract_body(msg)
    content = body_html or "<pre>" + frappe.utils.escape_html(body_text) + "</pre>"

    # Thread matching: In-Reply-To / References → existing Communication
    ref_doctype, ref_name = _match_thread(in_reply_to, references, sender_email)

    comm = frappe.new_doc("Communication")
    comm.communication_type = "Communication"
    comm.communication_medium = "Email"
    comm.sent_or_received = "Received"
    comm.subject = subject
    comm.sender = from_header
    comm.sender_full_name = _decode_mime_words(from_header.split("<")[0].strip().strip('"'))
    comm.content = content
    comm.text_content = body_text
    comm.message_id = message_id
    if in_reply_to:
        comm.in_reply_to = in_reply_to
    if ref_doctype:
        comm.reference_doctype = ref_doctype
        comm.reference_name = ref_name

    comm.insert(ignore_permissions=True)  # SYSTEM-INTERNAL: inbound webhook
    frappe.db.commit()

    _LOGGER.info(
        "SES inbound: Communication %s created (ref=%s %s)",
        comm.name, ref_doctype, ref_name,
    )

    # Story 2.4 — extract and store attachments
    _save_attachments(msg, comm.name)


def _match_thread(
    in_reply_to: str, references: str, sender_email: str
) -> tuple[str | None, str | None]:
    """Return (reference_doctype, reference_name) for this inbound email."""

    # 1. Match by In-Reply-To / References against existing Communication.message_id
    for mid in filter(None, [in_reply_to] + references.split()):
        mid = mid.strip()
        if not mid:
            continue
        row = frappe.db.get_value(
            "Communication",
            {"message_id": mid},
            ["reference_doctype", "reference_name"],
            as_dict=True,
        )
        if row and row.reference_doctype and row.reference_name:
            return row.reference_doctype, row.reference_name

    # 2. Match by sender email to a CRM Lead
    if sender_email:
        lead = frappe.db.get_value("CRM Lead", {"email": sender_email}, "name")
        if lead:
            return "CRM Lead", lead

    # 3. Auto-create Lead if configured
    settings = frappe.db.get_singles_dict("CRM SES Settings")
    if frappe.utils.cint(settings.get("create_lead_from_incoming_email")):
        lead_name = _create_lead_from_email(sender_email)
        if lead_name:
            return "CRM Lead", lead_name

    # 4. Unlinked — log and continue
    frappe.log_error(
        title="SES Inbound: Unmatched Email",
        message="sender=%s in_reply_to=%s" % (sender_email, in_reply_to),
    )
    return None, None


def _create_lead_from_email(sender_email: str) -> str | None:
    if not sender_email:
        return None
    try:
        lead = frappe.new_doc("CRM Lead")
        lead.email = sender_email
        # Parse name from email local part as best-effort fallback
        local = sender_email.split("@")[0].replace(".", " ").replace("_", " ").title()
        parts = local.split(None, 1)
        lead.first_name = parts[0]
        if len(parts) > 1:
            lead.last_name = parts[1]
        lead.source = "Inbound Email"
        lead.insert(ignore_permissions=True)  # SYSTEM-INTERNAL: inbound webhook
        frappe.db.commit()
        _LOGGER.info("SES inbound: auto-created Lead %s for %s", lead.name, sender_email)
        return lead.name
    except Exception as exc:
        _LOGGER.warning("SES inbound: failed to auto-create lead for %s: %s", sender_email, exc)
        return None


# ---------------------------------------------------------------------------
# Story 2.4 — Attachment extraction + Frappe File storage
# ---------------------------------------------------------------------------

def _save_attachments(msg, communication_name: str) -> None:
    for part in msg.walk():
        content_disposition = part.get_content_disposition() or ""
        if "attachment" not in content_disposition:
            continue

        filename = part.get_filename()
        if not filename:
            continue

        filename = _decode_mime_words(filename)
        filename = _sanitise_filename(filename)
        payload = part.get_payload(decode=True)
        if not payload:
            continue

        try:
            file_doc = frappe.new_doc("File")
            file_doc.file_name = filename
            file_doc.attached_to_doctype = "Communication"
            file_doc.attached_to_name = communication_name
            file_doc.content = payload
            file_doc.decode = False
            file_doc.is_private = 1
            file_doc.insert(ignore_permissions=True)  # SYSTEM-INTERNAL: inbound webhook
            frappe.db.commit()
            _LOGGER.info(
                "SES inbound: saved attachment %s on Communication %s",
                filename, communication_name,
            )
        except Exception as exc:
            frappe.log_error(
                title="SES Inbound: Attachment Save Failed",
                message="file=%s comm=%s error=%s" % (filename, communication_name, exc),
            )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _extract_body(msg) -> tuple[str, str]:
    """Return (html_body, text_body) from a parsed email.message.Message."""
    html_parts: list[str] = []
    text_parts: list[str] = []

    for part in msg.walk():
        ct = part.get_content_type()
        cd = part.get_content_disposition() or ""
        if "attachment" in cd:
            continue
        payload = part.get_payload(decode=True)
        if payload is None:
            continue
        charset = part.get_content_charset() or "utf-8"
        try:
            text = payload.decode(charset, errors="replace")
        except Exception:
            text = payload.decode("utf-8", errors="replace")

        if ct == "text/html":
            html_parts.append(text)
        elif ct == "text/plain":
            text_parts.append(text)

    return "\n".join(html_parts), "\n".join(text_parts)


def _decode_mime_words(value: str) -> str:
    if not value:
        return ""
    parts = decode_header(value)
    decoded = []
    for part, enc in parts:
        if isinstance(part, bytes):
            decoded.append(part.decode(enc or "utf-8", errors="replace"))
        else:
            decoded.append(part)
    return " ".join(decoded).strip()


def _sanitise_filename(name: str) -> str:
    # Strip path components, limit length
    name = re.sub(r"[/\\]", "_", name)
    name = re.sub(r"[^\w\s.\-]", "", name)
    return name[:255].strip() or "attachment"
