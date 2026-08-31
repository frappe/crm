# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class CRMMetaSettings(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		app_id: DF.Data | None
		app_secret: DF.Password | None
		connected_user_id: DF.Data | None
		connected_user_name: DF.Data | None
		user_access_token: DF.Password | None
		user_token_expires_at: DF.Datetime | None
		webhook_verify_token: DF.Data | None
	# end: auto-generated types

	def validate(self):
		if not self.webhook_verify_token:
			self.webhook_verify_token = frappe.generate_hash(length=32)
