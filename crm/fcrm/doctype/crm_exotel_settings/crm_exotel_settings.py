# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
import requests
from frappe import _
from frappe.model.document import Document


class CRMExotelSettings(Document):
	def validate(self):
		self.verify_credentials()

	def verify_credentials(self):
		if self.enabled:
			response = requests.get(
				"https://{subdomain}/v1/Accounts/{sid}".format(
					subdomain=self.subdomain, sid=self.account_sid
				),
				auth=(self.api_key, self.get_password("api_token")),
			)
			if response.status_code != 200:
				frappe.throw(
					_(f"Please enter valid exotel Account SID, API key & API token: {response.reason}"),
					title=_("Invalid credentials"),
				)
