# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class CRMFeedback(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		email: DF.Data | None
		feedback_type: DF.Literal["Feedback", "Question", "Bug Report", "Feature Request"]
		message: DF.SmallText
		status: DF.Literal["Open", "Reviewed", "Closed"]
		subject: DF.Data
		submitted_by: DF.Link | None

	# end: auto-generated types

	def before_insert(self):
		self.submitted_by = frappe.session.user
