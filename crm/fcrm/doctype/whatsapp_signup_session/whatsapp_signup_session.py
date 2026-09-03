# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from frappe.model.document import Document


class WhatsAppSignupSession(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		current_step: DF.Data | None
		details: DF.Code | None
		event: DF.Data | None
		outcome: DF.Literal["In Progress", "Completed", "Cancelled", "Error"]
		phone_number_id: DF.Data | None
		site_url: DF.Data | None
		waba_id: DF.Data | None
	# end: auto-generated types

	pass
