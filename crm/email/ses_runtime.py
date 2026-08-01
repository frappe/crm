"""CRM-owned AWS SES runtime configuration.

Self-contained: reads the **CRM SES Settings** Single DocType and exposes a
frozen `AwsSesRuntimeConfig` via a per-request cache. It has no dependency on any
other installed app — the previous implementation borrowed another app's send
stack and was therefore structurally dead on sites where that app was absent.

The send stack (`crm.email.ses_send`), the Email Queue subclass
(`crm.email.email_queue`), and the QueueBuilder patch (`crm.email.queue_patch`)
all consume `get_ses_runtime_config()`.
"""
from __future__ import annotations

from dataclasses import dataclass

import frappe
from frappe.utils import cint, cstr

_DOCTYPE = "CRM SES Settings"
_CACHE_KEY = "crm_ses_runtime_config_v1"

DEFAULT_RETRY_MODE = "standard"
DEFAULT_TOTAL_MAX_ATTEMPTS = 8
_VALID_RETRY_MODES = {"standard", "adaptive", "legacy"}


@dataclass(frozen=True)
class AwsSesRuntimeConfig:
	enabled: bool = False
	aws_region: str = ""
	default_sender_email: str = ""
	default_sender_name: str = ""
	sender_team_label: str = ""
	configuration_set_name: str = ""
	endpoint_url: str = ""
	profile_name: str = ""
	retry_mode: str = DEFAULT_RETRY_MODE
	total_max_attempts: int = DEFAULT_TOTAL_MAX_ATTEMPTS
	use_explicit_credentials: bool = False
	access_key_id: str = ""
	secret_access_key: str = ""
	session_token: str = ""


def clear_ses_runtime_config_cache() -> None:
	"""Drop the per-request cache so the next read reflects saved settings."""
	if getattr(frappe, "local", None) is not None:
		frappe.local.flags.pop(_CACHE_KEY, None)


def get_ses_runtime_config() -> AwsSesRuntimeConfig:
	"""Return the CRM SES runtime config, cached per request in `frappe.local.flags`."""
	cached = frappe.local.flags.get(_CACHE_KEY)
	if isinstance(cached, AwsSesRuntimeConfig):
		return cached

	config = _build_config()
	frappe.local.flags[_CACHE_KEY] = config
	return config


def _build_config() -> AwsSesRuntimeConfig:
	try:
		doc = frappe.get_cached_doc(_DOCTYPE, _DOCTYPE)
	except Exception:
		# DocType/singleton missing (pre-migrate) → disabled config; never raise here.
		return AwsSesRuntimeConfig()

	enabled = bool(cint(doc.get("enabled")))
	use_explicit = bool(cint(doc.get("use_explicit_credentials")))

	access_key_id = ""
	secret_access_key = ""
	session_token = ""
	if use_explicit:
		access_key_id = cstr(doc.get("access_key_id") or "").strip()
		secret_access_key = cstr(
			doc.get_password("secret_access_key", raise_exception=False) or ""
		).strip()
		session_token = cstr(
			doc.get_password("session_token", raise_exception=False) or ""
		).strip()

	retry_mode = cstr(doc.get("retry_mode") or DEFAULT_RETRY_MODE).strip().lower()
	if retry_mode not in _VALID_RETRY_MODES:
		retry_mode = DEFAULT_RETRY_MODE

	total_max_attempts = cint(doc.get("total_max_attempts")) or DEFAULT_TOTAL_MAX_ATTEMPTS
	if total_max_attempts < 1:
		total_max_attempts = DEFAULT_TOTAL_MAX_ATTEMPTS

	return AwsSesRuntimeConfig(
		enabled=enabled,
		aws_region=cstr(doc.get("aws_region")).strip(),
		default_sender_email=cstr(doc.get("default_sender_email")).strip(),
		default_sender_name=cstr(doc.get("default_sender_name")).strip(),
		sender_team_label=cstr(doc.get("sender_team_label")).strip(),
		configuration_set_name=cstr(doc.get("configuration_set_name")).strip(),
		endpoint_url=cstr(doc.get("endpoint_url")).strip(),
		profile_name=cstr(doc.get("profile_name")).strip(),
		retry_mode=retry_mode,
		total_max_attempts=total_max_attempts,
		use_explicit_credentials=use_explicit,
		access_key_id=access_key_id,
		secret_access_key=secret_access_key,
		session_token=session_token,
	)
