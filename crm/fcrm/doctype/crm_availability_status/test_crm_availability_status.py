# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from crm.install import add_default_availability_statuses


class TestCRMAvailabilityStatus(IntegrationTestCase):
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

	def test_renaming_a_status_tells_open_tabs(self):
		with patch(
			"crm.fcrm.doctype.crm_availability_status.crm_availability_status.publish_statuses_updated"
		) as publish:
			frappe.rename_doc("CRM Availability Status", "Away", "Stepped Out")

		publish.assert_called()
