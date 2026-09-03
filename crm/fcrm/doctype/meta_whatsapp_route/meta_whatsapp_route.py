# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from frappe.model.document import Document


class MetaWhatsAppRoute(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		display_phone_number: DF.Data | None
		last_forwarded_at: DF.Datetime | None
		phone_number_id: DF.Data | None
		site_url: DF.Data
		waba_id: DF.Data
	# end: auto-generated types

	pass
