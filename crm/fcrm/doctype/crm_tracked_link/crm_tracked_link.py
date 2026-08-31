# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import re

import frappe
from frappe import _
from frappe.model.document import Document


class CRMTrackedLink(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		click_count: DF.Int
		description: DF.SmallText | None
		slug: DF.Data
		target_url: DF.Data
	# end: auto-generated types

	def validate(self):
		self.slug = (self.slug or "").strip().lower()
		if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", self.slug):
			frappe.throw(_("Slug must contain only lowercase letters, numbers and hyphens"))
		if not (self.target_url or "").startswith(("http://", "https://")):
			frappe.throw(_("Target URL must start with http(s)://"))
