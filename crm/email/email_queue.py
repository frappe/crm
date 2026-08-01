from __future__ import annotations

import inspect
from typing import TYPE_CHECKING, Any

import frappe
from frappe.email.doctype.email_queue.email_queue import EmailQueue, SendMailContext
from frappe.utils import get_hook_method

from crm.email.ses_runtime import get_ses_runtime_config

if TYPE_CHECKING:
	from frappe.email.frappemail import FrappeMail
	from frappe.email.smtp import SMTPServer
else:
	FrappeMail = Any
	SMTPServer = Any


class CrmSesAwareEmailQueue(EmailQueue):
	"""Email Queue controller that skips native prefetch only in SES-enabled mode."""

	def _is_ses_enabled(self) -> bool:
		return bool(get_ses_runtime_config().enabled)

	def send(
		self,
		smtp_server_instance: SMTPServer = None,
		frappe_mail_client: FrappeMail = None,
		force_send: bool = False,
	):
		if not self._is_ses_enabled():
			return EmailQueue.send(
				self,
				smtp_server_instance=smtp_server_instance,
				frappe_mail_client=frappe_mail_client,
				force_send=force_send,
			)

		if not self.can_send_now() and not force_send:
			return

		with self._build_send_mail_context(smtp_server_instance, frappe_mail_client) as ctx:
			override_send = get_hook_method("override_email_send")
			if not override_send:
				ctx.fetch_outgoing_server()

			message = None
			for recipient in self.recipients:
				if recipient.is_mail_sent():
					continue

				message = ctx.build_message(recipient.recipient)
				if override_send:
					override_send(self, self.sender, recipient.recipient, message)
				elif not self._is_test_send_context():
					if ctx.email_account_doc.service == "Frappe Mail":
						is_newsletter = self.reference_doctype == "Newsletter"
						ctx.frappe_mail_client.send_raw(
							sender=self.sender,
							recipients=recipient.recipient,
							message=message,
							is_newsletter=is_newsletter,
						)
					else:
						ctx.smtp_server.session.sendmail(
							from_addr=self.sender,
							to_addrs=recipient.recipient,
							msg=message.decode("utf-8").encode(),
						)

				ctx.update_recipient_status_to_sent(recipient)

			if self._is_test_capture_mode():
				flags = getattr(frappe, "flags", None)
				if flags is not None:
					flags.sent_mail = message
				return

			if not override_send and ctx.email_account_doc.append_emails_to_sent_folder:
				ctx.email_account_doc.append_email_to_sent_folder(message)

	def _build_send_mail_context(
		self, smtp_server_instance: SMTPServer = None, frappe_mail_client: FrappeMail = None
	):
		try:
			parameters = list(inspect.signature(SendMailContext.__init__).parameters.values())[1:]
		except (TypeError, ValueError):
			parameters = []

		has_varargs = any(p.kind == inspect.Parameter.VAR_POSITIONAL for p in parameters)
		positional_slots = [
			p
			for p in parameters
			if p.kind in (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD)
		]
		has_frappe_mail_kwarg = any(p.name == "frappe_mail_client" for p in parameters)

		if has_varargs or len(positional_slots) >= 3:
			return SendMailContext(self, smtp_server_instance, frappe_mail_client)

		if has_frappe_mail_kwarg:
			return SendMailContext(
				self,
				smtp_server_instance,
				frappe_mail_client=frappe_mail_client,
			)

		return SendMailContext(self, smtp_server_instance)

	def _is_test_send_context(self) -> bool:
		in_test = bool(getattr(frappe, "in_test", False))
		flags = getattr(frappe, "flags", None)
		testing_email = bool(getattr(flags, "testing_email", False))
		return bool(in_test and not testing_email)

	def _is_test_capture_mode(self) -> bool:
		return self._is_test_send_context()
