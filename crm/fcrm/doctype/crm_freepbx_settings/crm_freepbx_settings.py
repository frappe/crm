import frappe
from frappe.model.document import Document


class CRMFreePBXSettings(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		enabled: DF.Check
		host: DF.Data | None
		record_call: DF.Check
		ws_port: DF.Int
		wss_port: DF.Int
	# end: auto-generated types

	pass
