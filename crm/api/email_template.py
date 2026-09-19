import html
import re

import frappe
from frappe import _
from frappe.email.doctype.email_template.email_template import (
	get_email_template as _get_email_template,
)
from frappe.utils import validate_email_address
from jinja2.exceptions import TemplateError


@frappe.whitelist()
def get_email_template(template_name: str, doc: dict | str, sender: str | None = None) -> dict:
	"""Render an email template, surfacing Jinja errors as a user-facing message.

	When a template references something that isn't in the context (e.g.
	`{{ customer.name }}`), `frappe.render_template` msgprints the raw traceback
	and re-raises the Jinja error, which the client can only show as a 500.
	Replace that with a short validation error naming the template and the reason.
	"""
	if isinstance(doc, str):
		doc = frappe.parse_json(doc)
	if not isinstance(doc, dict):
		frappe.throw(_("Invalid document context"))

	if not frappe.db.exists("Email Template", template_name):
		frappe.throw(_("Email Template {0} not found").format(template_name), frappe.DoesNotExistError)

	if sender and not validate_email_address(sender):
		frappe.throw(_("Invalid sender email address"))

	try:
		return _get_email_template(template_name, doc, sender=sender)
	except TemplateError as e:
		# drop the traceback that frappe.render_template already msgprint'ed
		frappe.clear_last_message()
		frappe.throw(
			_("Could not apply email template {0}: {1}").format(template_name, _jinja_error_reason(e)),
			title=_("Invalid Email Template"),
		)


def _jinja_error_reason(e: TemplateError) -> str:
	"""Extract e.g. `'customer' is undefined` from the exception.

	`frappe.render_template` overwrites the exception message with a `<pre>`
	wrapped traceback, so the original Jinja message is only on its last line.
	"""
	text = html.unescape(re.sub(r"</?pre>", "", str(e))).strip()
	last_line = text.splitlines()[-1] if text else ""
	# "jinja2.exceptions.UndefinedError: 'customer' is undefined" -> "'customer' is undefined"
	return last_line.split(": ", 1)[-1] or e.__class__.__name__
