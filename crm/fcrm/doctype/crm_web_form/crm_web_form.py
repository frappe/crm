# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import re

import frappe
from frappe import _
from frappe.model.document import Document

# DocTypes a web form is allowed to create records in. Kept tight because
# submissions run as Guest — see crm/api/web_form.py.
ALLOWED_DOCTYPES = ("CRM Lead", "CRM Deal")


class CRMWebForm(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from crm.fcrm.doctype.crm_web_form_field.crm_web_form_field import CRMWebFormField

		description: DF.SmallText | None
		document_type: DF.Link
		fields: DF.Table[CRMWebFormField]
		published: DF.Check
		route: DF.Data
		submit_button_label: DF.Data | None
		success_message: DF.SmallText | None
		title: DF.Data
	# end: auto-generated types

	def validate(self):
		self.set_route()
		self.validate_document_type()

	def set_route(self):
		if not self.route and self.title:
			self.route = self.title
		self.route = slugify(self.route or "")
		if not self.route:
			frappe.throw(_("Route is required"))

	def validate_document_type(self):
		if self.document_type not in ALLOWED_DOCTYPES:
			frappe.throw(
				_("Web forms can only map to: {0}").format(", ".join(ALLOWED_DOCTYPES))
			)


def slugify(value: str) -> str:
	value = (value or "").strip().lower()
	value = re.sub(r"[^a-z0-9]+", "-", value)
	return value.strip("-")
