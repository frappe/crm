# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

from crm.api.availability import publish_availability, publish_statuses_updated


class CRMAvailabilityStatus(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		availability_status: DF.Data
		category: DF.Literal["Active", "Away", "Unavailable"]
		color: DF.Literal[
			"black",
			"gray",
			"blue",
			"green",
			"red",
			"pink",
			"orange",
			"amber",
			"yellow",
			"cyan",
			"teal",
			"violet",
			"purple",
		]
		enabled: DF.Check
		position: DF.Int
	# end: auto-generated types

	def validate(self):
		before = self.get_doc_before_save()
		was_active = before and before.enabled and before.category == "Active"
		if was_active and not (self.enabled and self.category == "Active"):
			self.ensure_another_active_status()

	def on_update(self):
		if not self.enabled and self.has_value_changed("enabled") and not self.is_new():
			self.clear_from_users()
		publish_statuses_updated()

	def on_trash(self):
		if self.enabled and self.category == "Active":
			self.ensure_another_active_status()

	def after_delete(self):
		publish_statuses_updated()

	def after_rename(self, old, new, merge=False):
		publish_statuses_updated()

	def ensure_another_active_status(self):
		# users with no status count as Active, so one must always be pickable
		if not frappe.db.exists(
			"CRM Availability Status",
			{"category": "Active", "enabled": 1, "name": ["!=", self.name]},
		):
			frappe.throw(_("Keep at least one enabled status in the Active category."))

	def clear_from_users(self):
		for user in frappe.get_all("User", {"crm_availability": self.name}, pluck="name"):
			frappe.db.set_value(
				"User",
				user,
				{
					"crm_availability": None,
					"crm_availability_changed_on": frappe.utils.now(),
					"crm_availability_changed_by": frappe.session.user,
				},
			)
			publish_availability(user)
