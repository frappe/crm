# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class FacebookLeadForm(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from crm.lead_syncing.doctype.facebook_lead_form_question.facebook_lead_form_question import FacebookLeadFormQuestion
		from frappe.types import DF

		form_name: DF.Data | None
		id: DF.Data | None
		page: DF.Link
		questions: DF.Table[FacebookLeadFormQuestion]
	# end: auto-generated types

	pass
