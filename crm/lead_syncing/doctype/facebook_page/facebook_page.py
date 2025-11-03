# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class FacebookPage(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		access_token: DF.SmallText | None
		account_id: DF.Data | None
		category: DF.Data | None
		id: DF.Data | None
		page_name: DF.Data | None
	# end: auto-generated types

	pass
