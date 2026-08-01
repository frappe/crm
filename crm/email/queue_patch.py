from __future__ import annotations

from email.utils import formataddr
import logging

import frappe

from crm.email.ses_runtime import AwsSesRuntimeConfig, get_ses_runtime_config

_PATCH_FLAG = "_crm_ses_decoupler_patched"
_ORIGINAL_GET_OUTGOING = "_crm_original_get_outgoing_email_account"
_ORIGINAL_SEND_EMAILS = "_crm_original_send_emails"
_LOGGER = logging.getLogger(__name__)

try:
	from frappe.email.doctype.email_queue.email_queue import EmailQueue, QueueBuilder
except Exception:
	EmailQueue = None
	QueueBuilder = None


class _SyntheticEmailAccount:
	"""Minimal Email Account-like object used for MIME build in SES mode."""

	def __init__(self, config: AwsSesRuntimeConfig):
		sender_email = (config.default_sender_email or "").strip()
		sender_name = (config.default_sender_name or "").strip() or sender_email

		if not sender_email:
			frappe.throw(
				"CRM SES Settings requires Default Sender Email when override is enabled.",
				title="SES Sender Missing",
			)

		self.name = sender_name
		self.email_id = sender_email
		self.always_bcc = None
		self.add_signature = 0
		self.signature = ""
		self.footer = ""
		self.brand_logo = None
		self.track_email_status = 0
		self.append_emails_to_sent_folder = 0
		self.always_use_account_email_id_as_sender = 0
		self.always_use_account_name_as_sender_name = 0
		self.add_reply_to_header = 1
		self.add_x_original_from = 0
		self.reply_to_addresses = []

	@property
	def default_sender(self) -> str:
		return formataddr((self.name, self.email_id))

	def get(self, key: str, default=None):
		return getattr(self, key, default)

	def is_exists_in_db(self) -> bool:
		return False


def _is_ses_decoupled_mode() -> bool:
	return bool(get_ses_runtime_config().enabled)


def _patched_get_outgoing_email_account(self):
	if not _is_ses_decoupled_mode():
		original = getattr(self.__class__, _ORIGINAL_GET_OUTGOING)
		return original(self)

	if getattr(self, "_email_account", None):
		return self._email_account

	self._email_account = _SyntheticEmailAccount(get_ses_runtime_config())
	return self._email_account


def _patched_send_emails(self, queue_data, final_recipients):
	if not _is_ses_decoupled_mode():
		original = getattr(self.__class__, _ORIGINAL_SEND_EMAILS)
		return original(self, queue_data, final_recipients)

	email_queue_cls, _queue_builder_cls = _resolve_email_queue_components()

	for recipient in final_recipients:
		recipients = list(set([recipient, *self.final_cc(), *self.final_bcc()]))
		queue_doc = email_queue_cls.new({**queue_data, **{"recipients": recipients}}, ignore_permissions=True)
		try:
			queue_doc.send()
		except Exception as exc:
			frappe.log_error(
				title="CRM SES Bulk Queue Send Failure",
				message=(
					f"recipient={recipient}\n"
					f"queue={getattr(queue_doc, 'name', '')}\n"
					f"error_type={type(exc).__name__}\n"
					f"error={exc}\n"
					f"traceback={frappe.get_traceback()}"
				),
			)


def _resolve_email_queue_components():
	global EmailQueue, QueueBuilder
	if EmailQueue is not None and QueueBuilder is not None:
		return EmailQueue, QueueBuilder

	from frappe.email.doctype.email_queue.email_queue import EmailQueue as _EmailQueue, QueueBuilder as _QueueBuilder

	EmailQueue, QueueBuilder = _EmailQueue, _QueueBuilder
	return EmailQueue, QueueBuilder


def apply_queue_builder_patches():
	"""Apply QueueBuilder patches once per process."""
	try:
		_email_queue_cls, queue_builder_cls = _resolve_email_queue_components()
	except Exception as exc:
		_LOGGER.exception("Skipping SES QueueBuilder patch due to import failure: %s", exc)
		return False

	if getattr(queue_builder_cls, _PATCH_FLAG, False):
		return True

	setattr(queue_builder_cls, _ORIGINAL_GET_OUTGOING, queue_builder_cls.get_outgoing_email_account)
	setattr(queue_builder_cls, _ORIGINAL_SEND_EMAILS, queue_builder_cls.send_emails)
	queue_builder_cls.get_outgoing_email_account = _patched_get_outgoing_email_account
	queue_builder_cls.send_emails = _patched_send_emails
	setattr(queue_builder_cls, _PATCH_FLAG, True)
	return True
