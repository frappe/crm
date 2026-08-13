# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import get_datetime


class CRMYeastarSettings(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		access_token: DF.Data | None
		access_token_expire_duration: DF.Int
		access_token_expiry: DF.Datetime | None
		access_token_issue: DF.Datetime | None
		enabled: DF.Check
		password: DF.Password | None
		refresh_token: DF.Data | None
		refresh_token_expire_duration: DF.Int
		refresh_token_expiry: DF.Datetime | None
		refresh_token_issue: DF.Datetime | None
		url: DF.Data | None
		username: DF.Data | None
	# end: auto-generated types

	pass

	def validate(self):
		self.clean_url()

	def clean_url(self):
		self.url = self.url.rstrip("/")

	@frappe.whitelist()
	def generate_access_token(self) -> bool:
		return self.access_token if not self.is_token_expired else self.apply_token()

	def apply_token(self) -> str:
		from crm.integrations.yeastar.services import TokenService

		return TokenService(settings_doc=self).issue_token()

	@property
	def is_token_expired(self) -> bool:
		return bool(get_datetime(self.access_token_expiry) < get_datetime())
