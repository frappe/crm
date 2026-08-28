"""CRM-owned outbound transport for `override_email_send`.

Wired from `crm/hooks.py`:

    override_email_send = "crm.email.ses_send.send"

Frappe calls `send()` once per recipient from `EmailQueue.send`. When CRM SES
Settings is enabled we ship the raw MIME bytes to Amazon SES (v1 `send_raw_email`,
or v2 `send_email` for large payloads), after rewriting the `From` header to the
configured / dynamically-composed sender identity. When SES is disabled we fall
back to the native SMTP / Frappe Mail path so non-SES installs are unaffected.
"""
from __future__ import annotations

from email.parser import BytesParser
from email.policy import SMTP
from email.utils import formataddr, parseaddr

import frappe

from crm.email.ses_runtime import AwsSesRuntimeConfig, get_ses_runtime_config

# SES raw-message size ceilings (base64-inflated MIME).
SES_V1_MAX_RAW_MESSAGE_BYTES = 10 * 1024 * 1024
SES_V2_MAX_RAW_MESSAGE_BYTES = 40 * 1024 * 1024

# Display-name values that must never leak into a "Name from X" string.
_JUNK_LABELS = {"", "none", "null", "undefined"}


def send(queue_doc, sender: str, recipient: str, message: bytes):
	"""Hook target for `override_email_send`. Called once per recipient."""
	if _should_skip_external_send_in_tests():
		return

	state = _get_runtime_state(queue_doc)
	config = get_ses_runtime_config()
	transport = "native"

	try:
		payload = _ensure_bytes(message)
		if not config.enabled:
			_send_via_native(queue_doc, sender, recipient, payload, state)
			return

		# SES path taken — label the transport now so a validation failure below is
		# reported as an SES error, not "native".
		transport = "ses"
		_validate_runtime_config(config)

		payload_size = len(payload)
		if payload_size > SES_V2_MAX_RAW_MESSAGE_BYTES:
			transport = "ses"
			frappe.throw(
				"Email payload is too large for Amazon SES transport. "
				"Size: %d bytes, max: %d bytes." % (payload_size, SES_V2_MAX_RAW_MESSAGE_BYTES)
			)

		if payload_size > SES_V1_MAX_RAW_MESSAGE_BYTES:
			transport = "sesv2"
			_send_via_ses_v2(queue_doc, recipient, payload, config, state)
		else:
			transport = "sesv1"
			_send_via_ses_v1(queue_doc, recipient, payload, config, state)
	except Exception as exc:
		_log_send_error(queue_doc, recipient, transport, exc)
		raise


# ---------------------------------------------------------------------------
# Validation & test guards
# ---------------------------------------------------------------------------

def _validate_runtime_config(config: AwsSesRuntimeConfig) -> None:
	if not config.aws_region:
		frappe.throw(
			"CRM SES Settings is enabled but AWS Region is not configured.",
			title="AWS SES Region Missing",
		)
	if not config.default_sender_email:
		frappe.throw(
			"CRM SES Settings is enabled but Sender Email is not configured.",
			title="AWS SES Sender Missing",
		)
	if config.use_explicit_credentials:
		missing = []
		if not config.access_key_id:
			missing.append("Access Key ID")
		if not config.secret_access_key:
			# Empty here (not a decrypt error — that surfaces as InvalidToken, not this
			# throw) means the Password field was never saved, or was cleared. The most
			# common cause is entering the key but leaving the Secret Access Key blank.
			missing.append("Secret Access Key")
		if missing:
			frappe.throw(
				"CRM SES Settings has 'Use Explicit Credentials' enabled but "
				+ " and ".join(missing)
				+ " is not saved. Open CRM SES Settings, re-enter the "
				+ " and ".join(missing)
				+ ", and Save — or uncheck 'Use Explicit Credentials' to use the "
				"instance IAM role / AWS profile instead.",
				title="AWS SES Credentials Missing",
			)


def _should_skip_external_send_in_tests() -> bool:
	flags = getattr(frappe, "flags", None)
	testing_email = bool(getattr(flags, "testing_email", False))
	in_test = bool(getattr(frappe, "in_test", False))
	return bool(in_test and not testing_email)


def _get_runtime_state(queue_doc) -> dict:
	state = getattr(queue_doc, "_crm_ses_override_state", None)
	if isinstance(state, dict):
		return state
	state = {}
	setattr(queue_doc, "_crm_ses_override_state", state)
	return state


def _ensure_bytes(message) -> bytes:
	if message is None:
		return b""
	if isinstance(message, bytes):
		return message
	return str(message).encode("utf-8")


# ---------------------------------------------------------------------------
# Native fallback (SES disabled)
# ---------------------------------------------------------------------------

def _send_via_native(queue_doc, sender: str, recipient: str, message: bytes, state: dict) -> None:
	if "email_account_doc" not in state:
		try:
			state["email_account_doc"] = queue_doc.get_email_account(raise_error=True)
		except Exception:
			frappe.throw(
				"CRM SES override is disabled and no outgoing Email Account is configured. "
				"Enable SES in CRM SES Settings, or add an outgoing Email Account.",
				title="Outgoing Email Account Missing",
			)

	email_account_doc = state["email_account_doc"]

	if email_account_doc.service == "Frappe Mail":
		if "frappe_mail_client" not in state:
			state["frappe_mail_client"] = email_account_doc.get_frappe_mail_client()
		is_newsletter = queue_doc.reference_doctype == "Newsletter"
		state["frappe_mail_client"].send_raw(
			sender=sender,
			recipients=recipient,
			message=message,
			is_newsletter=is_newsletter,
		)
		return

	if "smtp_server" not in state:
		state["smtp_server"] = email_account_doc.get_smtp_server()

	smtp_message = message
	try:
		smtp_message = message.decode("utf-8").encode()
	except Exception:
		pass

	state["smtp_server"].session.sendmail(
		from_addr=sender,
		to_addrs=recipient,
		msg=smtp_message,
	)


# ---------------------------------------------------------------------------
# SES transports
# ---------------------------------------------------------------------------

def _send_via_ses_v1(queue_doc, recipient: str, message: bytes, config: AwsSesRuntimeConfig, state: dict) -> None:
	payload = _apply_configured_sender(message, config)
	client = _get_ses_client(config, state)
	kwargs = {
		"Destinations": [recipient],
		"RawMessage": {"Data": payload},
	}
	if config.default_sender_email:
		kwargs["Source"] = config.default_sender_email
	if config.configuration_set_name:
		kwargs["ConfigurationSetName"] = config.configuration_set_name

	response = client.send_raw_email(**kwargs)
	_log_send_success(queue_doc, recipient, "sesv1", response.get("MessageId"))


def _send_via_ses_v2(queue_doc, recipient: str, message: bytes, config: AwsSesRuntimeConfig, state: dict) -> None:
	payload = _apply_configured_sender(message, config)
	client = _get_sesv2_client(config, state)
	kwargs = {
		"Destination": {"ToAddresses": [recipient]},
		"Content": {"Raw": {"Data": payload}},
	}
	if config.default_sender_email:
		kwargs["FromEmailAddress"] = config.default_sender_email
	if config.configuration_set_name:
		kwargs["ConfigurationSetName"] = config.configuration_set_name

	response = client.send_email(**kwargs)
	_log_send_success(queue_doc, recipient, "sesv2", response.get("MessageId"))


# ---------------------------------------------------------------------------
# Sender identity (E3-S1: dynamic sender name with graceful degradation)
# ---------------------------------------------------------------------------

def _clean_label(value) -> str:
	"""Return a display-safe label, or "" if the value is junk (None/null/empty)."""
	text = (value or "").strip()
	return "" if text.lower() in _JUNK_LABELS else text


def _brand_name() -> str:
	"""Team label fallback: FCRM Settings brand_name (never 'None'/'Null')."""
	try:
		return _clean_label(frappe.db.get_single_value("FCRM Settings", "brand_name"))
	except Exception:
		return ""


def _current_user_full_name() -> str:
	"""Full name of the eligible (non-system) session user, else ""."""
	user = getattr(frappe.session, "user", None)
	if not user or user in ("Administrator", "Guest", ""):
		return ""
	try:
		return _clean_label(frappe.db.get_value("User", user, "full_name"))
	except Exception:
		return ""


def _resolve_display_name(config: AwsSesRuntimeConfig) -> str:
	"""Compose the From display name.

	Precedence & graceful degradation (never emits 'Name from None'):
	  1. explicit Default Sender Name        → use verbatim
	  2. user full name + valid team label   → "Salim from Careverse Team"
	  3. user full name, no valid team       → "Salim"
	  4. no user + valid team label          → "Careverse Team"
	  5. nothing usable                      → "" (bare email address)
	"""
	explicit = _clean_label(config.default_sender_name)
	if explicit:
		return explicit

	team = _clean_label(config.sender_team_label) or _brand_name()
	user_name = _current_user_full_name()

	if user_name and team:
		return user_name + " from " + team  # nosec B608 — internal strings, not HTML
	if user_name:
		return user_name
	if team:
		return team
	return ""


def _apply_configured_sender(message: bytes, config: AwsSesRuntimeConfig) -> bytes:
	"""Rewrite the From header to the CRM SES sender identity.

	Preserves the original From as Reply-To (unless one is already set) so replies
	still reach the human who sent the mail.
	"""
	payload = _ensure_bytes(message)
	static_email = (config.default_sender_email or "").strip()
	if not static_email:
		return payload

	display_name = _resolve_display_name(config)
	effective_from = formataddr((display_name, static_email)) if display_name else static_email

	try:
		parsed = BytesParser(policy=SMTP).parsebytes(payload)
	except Exception:
		return payload

	original_from = (parsed.get("From") or "").strip()
	reply_to = (parsed.get("Reply-To") or "").strip()
	original_addr = parseaddr(original_from)[1]
	if original_addr and original_addr != static_email and not reply_to:
		parsed["Reply-To"] = original_from

	if "From" in parsed:
		parsed.replace_header("From", effective_from)
	else:
		parsed["From"] = effective_from

	return parsed.as_bytes(policy=SMTP)


# ---------------------------------------------------------------------------
# boto3 clients
# ---------------------------------------------------------------------------

def _get_ses_client(config: AwsSesRuntimeConfig, state: dict):
	if "ses_client" not in state:
		session = _get_boto3_session(config, state)
		state["ses_client"] = session.client(
			"ses",
			region_name=config.aws_region,
			endpoint_url=config.endpoint_url or None,
			config=_get_botocore_config(config),
		)
	return state["ses_client"]


def _get_sesv2_client(config: AwsSesRuntimeConfig, state: dict):
	if "sesv2_client" not in state:
		session = _get_boto3_session(config, state)
		state["sesv2_client"] = session.client(
			"sesv2",
			region_name=config.aws_region,
			endpoint_url=config.endpoint_url or None,
			config=_get_botocore_config(config),
		)
	return state["sesv2_client"]


def _get_boto3_session(config: AwsSesRuntimeConfig, state: dict):
	if "boto3_session" in state:
		return state["boto3_session"]

	import boto3

	session_kwargs = {}
	if config.profile_name:
		session_kwargs["profile_name"] = config.profile_name
	if config.aws_region:
		session_kwargs["region_name"] = config.aws_region
	if config.use_explicit_credentials:
		session_kwargs["aws_access_key_id"] = config.access_key_id
		session_kwargs["aws_secret_access_key"] = config.secret_access_key
		if config.session_token:
			session_kwargs["aws_session_token"] = config.session_token

	session = boto3.Session(**session_kwargs)
	state["boto3_session"] = session
	return session


def _get_botocore_config(config: AwsSesRuntimeConfig):
	from botocore.config import Config

	return Config(
		retries={
			"mode": config.retry_mode,
			"total_max_attempts": config.total_max_attempts,
		}
	)


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

def _log_send_success(queue_doc, recipient: str, transport: str, message_id) -> None:
	frappe.logger("crm.ses").info(
		"queue=%s recipient=%s transport=%s message_id=%s",
		getattr(queue_doc, "name", ""),
		recipient,
		transport,
		message_id or "",
	)


def _log_send_error(queue_doc, recipient: str, transport: str, exc: Exception) -> None:
	frappe.log_error(
		title="CRM SES Send Failure",
		message="\n".join([
			"CRM SES override send failed",
			"queue=" + getattr(queue_doc, "name", ""),
			"recipient=" + recipient,
			"transport=" + transport,
			"error_type=" + type(exc).__name__,
			"error=" + str(exc),
		]),
	)
