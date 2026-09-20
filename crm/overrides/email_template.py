import html
import re

import frappe
from frappe import _
from frappe.email.doctype.email_template.email_template import EmailTemplate
from frappe.model import default_fields
from jinja2 import meta, nodes
from jinja2.exceptions import TemplateError


class CustomEmailTemplate(EmailTemplate):
	def validate(self):
		super().validate()
		self.validate_template_variables()

	def validate_template_variables(self):
		"""Reject variables that don't exist on the reference doctype.

		Templates are rendered with the doc's fields as the context (and the doc
		itself nested as `doc`), so `{{ first_name }}` and `{{ doc.first_name }}`
		both work. Anything else (`{{ lead.first_name }}`, `{{ doc.emial }}`) would
		only fail later, when a user tries to apply the template to an email.
		"""
		if not self.reference_doctype:
			return

		known = self.get_template_context_keys()
		jenv = frappe.get_jenv()
		unknown = set()

		for template in (self.subject, self.response_):
			if not template:
				continue
			ast = jenv.parse(template)
			unknown |= meta.find_undeclared_variables(ast) - known - set(jenv.globals)
			unknown |= {
				f"doc.{node.attr}"
				for node in ast.find_all(nodes.Getattr)
				if isinstance(node.node, nodes.Name) and node.node.name == "doc" and node.attr not in known
			}

		if unknown:
			frappe.throw(
				_("{0} has no field(s) named: {1}").format(
					frappe.bold(self.reference_doctype), ", ".join(sorted(unknown))
				),
				title=_("Unknown Template Variable"),
			)

	def get_template_context_keys(self):
		fieldnames = {df.fieldname for df in frappe.get_meta(self.reference_doctype).fields}
		# `doc` is nested by the email editor; signature/footer are injected by
		# `inject_email_account` for html templates
		return fieldnames | set(default_fields) | {"doc", "email_signature", "email_footer"}

	def get_formatted_email(self, doc, sender=None):
		try:
			return super().get_formatted_email(doc, sender=sender)
		except TemplateError as e:
			# frappe.render_template already msgprint'ed the raw traceback; replace it
			frappe.clear_last_message()
			frappe.throw(
				_("Could not apply email template {0}: {1}").format(
					frappe.bold(self.name), get_jinja_error_reason(e)
				),
				title=_("Invalid Email Template"),
			)

	@staticmethod
	def default_list_data():
		columns = [
			{
				"label": "Name",
				"type": "Data",
				"key": "name",
				"width": "17rem",
			},
			{
				"label": "Subject",
				"type": "Data",
				"key": "subject",
				"width": "12rem",
			},
			{
				"label": "Enabled",
				"type": "Check",
				"key": "enabled",
				"width": "6rem",
			},
			{
				"label": "Doctype",
				"type": "Link",
				"key": "reference_doctype",
				"width": "12rem",
			},
			{
				"label": "Last Modified",
				"type": "Datetime",
				"key": "modified",
				"width": "8rem",
			},
		]
		rows = [
			"name",
			"enabled",
			"use_html",
			"reference_doctype",
			"subject",
			"response",
			"response_html",
			"modified",
		]
		return {"columns": columns, "rows": rows}


def get_jinja_error_reason(e: TemplateError) -> str:
	"""Extract e.g. `'lead' is undefined` from a render error.

	`frappe.render_template` overwrites the exception message with a `<pre>`
	wrapped traceback, so the original Jinja message is only on its last line.
	"""
	text = html.unescape(re.sub(r"</?pre>", "", str(e))).strip()
	last_line = text.splitlines()[-1] if text else ""
	# "jinja2.exceptions.UndefinedError: 'lead' is undefined" -> "'lead' is undefined"
	return last_line.split(": ", 1)[-1] or e.__class__.__name__
