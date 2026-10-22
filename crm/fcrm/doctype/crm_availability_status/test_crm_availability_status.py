# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe

from crm.install import add_default_availability_statuses
from crm.tests import CRMTestCase


class TestCRMAvailabilityStatus(CRMTestCase):
	def setUp(self):
		add_default_availability_statuses()

	def test_last_active_status_cannot_be_disabled(self):
		for name in frappe.get_all("CRM Availability Status", {"category": "Active"}, pluck="name"):
			if name != "Active":
				frappe.db.set_value("CRM Availability Status", name, "enabled", 0)

		status = frappe.get_doc("CRM Availability Status", "Active")
		status.enabled = 0
		self.assertRaises(frappe.ValidationError, status.save)

	def test_disabling_a_status_clears_it_from_users(self):
		frappe.db.set_value("User", "Administrator", "crm_availability", "Away")

		status = frappe.get_doc("CRM Availability Status", "Away")
		status.enabled = 0
		status.save()

		self.assertFalse(frappe.db.get_value("User", "Administrator", "crm_availability"))
