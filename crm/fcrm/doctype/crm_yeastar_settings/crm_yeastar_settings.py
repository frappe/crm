# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import requests
import json


class CRMYeastarSettings(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		access_token: DF.Data | None
		enabled: DF.Check
		password: DF.Data | None
		refresh_token: DF.Data | None
		request_url: DF.Data | None
		username: DF.Data | None

	# end: auto-generated types
	pass

	def validate(self):
		if self.enabled:
			if self.generate_access_token():
				frappe.msgprint("Access token generated successfully.")

	def generate_access_token(self) -> bool:

		request_url: str = self.request_url + "/get_token"

		try:
			payload = {
				"username": self.username,
				"password": self.password,
			}

			response = requests.post(
				request_url,
				data=json.dumps(payload),
				headers={"Content-Type": "application/json"},
			)

			response.raise_for_status()

			data = response.json()

			if data.get("errcode") != 0:
				frappe.throw(
					f"Error from Yeastar API: {data.get('errmsg', 'Unknown error')}"
				)

			self.access_token = data.get("access_token")
			self.refresh_token = data.get("refresh_token")

			return True

		except Exception as e:
			frappe.log_error(
				frappe.get_traceback(),
				f"Yeastar CRM Settings: Access Token Generation Failed, {str(e)}",
			)
			frappe.throw(
				"Failed to generate access token for Yeastar CRM. Please check the logs for more details."
			)
