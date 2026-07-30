# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class CRMAvayaSettings(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		account_id: DF.Data | None
		aes_host: DF.Data | None
		axp_base_url: DF.Data | None
		axp_region: DF.Data | None
		client_id: DF.Data | None
		client_secret: DF.Password | None
		cm_id: DF.Data | None
		connector_endpoint: DF.Data | None
		cti_password: DF.Password | None
		cti_user: DF.Data | None
		dmcc_or_tsapi_link: DF.Data | None
		enabled: DF.Check
		mode: DF.Literal["Cloud (AXP)", "On-Prem (Aura/AES)"]
		recorder_auth: DF.Password | None
		recorder_base_url: DF.Data | None
		record_calls: DF.Check
		webhook_verify_token: DF.Password | None
	# end: auto-generated types

	def validate(self):
		# Live credential verification is an E5/E6 concern (gated on Tiberbu's Avaya
		# edition + credentials). The mandatory_depends_on rules in the JSON already
		# enforce that the required fields for the selected mode are filled before save,
		# so there is nothing to verify here yet. Kept as an explicit hook so E5 can add
		# an AXP/AES reachability check without changing the doctype shape.
		pass
