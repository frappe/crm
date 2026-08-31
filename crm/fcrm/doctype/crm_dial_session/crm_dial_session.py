# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from frappe.model.document import Document


class CRMDialSession(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from crm.fcrm.doctype.crm_dial_session_entry.crm_dial_session_entry import CRMDialSessionEntry

		agent: DF.Link
		entries: DF.Table[CRMDialSessionEntry]
		source_doctype: DF.Literal["CRM Lead", "CRM Deal"]
		status: DF.Literal["In Progress", "Completed", "Cancelled"]
		title: DF.Data | None
	# end: auto-generated types

	pass
