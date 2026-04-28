import frappe
from frappe.model.document import Document


class CRMFreePBXSettings(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		enabled: DF.Check
		flask_application_auth_token: DF.Data | None
		flask_application_url: DF.Data | None
		host: DF.Data | None
		record_call: DF.Check
		ws_port: DF.Int
		wss_port: DF.Int
	# end: auto-generated types

	pass
