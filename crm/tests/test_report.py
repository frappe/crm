# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import json

import frappe
from frappe.tests import IntegrationTestCase

from crm.api.report import (
	_filter_permitted_reports,
	_validate_fcrm_report,
	export_report,
	get_fcrm_reports,
	get_pinned_reports,
	get_report_data,
	get_report_meta,
	pin_report,
	pin_reports,
	unpin_report,
)

TEST_FCRM_REPORT = "FCRM Test Report"
NON_FCRM_TEST_REPORT = "Non FCRM Test Report"
REPORT_BUILDER_TEST_REPORT = "Report Builder Test Report"
PREPARED_TEST_REPORT = "Prepared Test Report"
DISABLED_TEST_REPORT = "Disabled Test Report"


class TestReport(IntegrationTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		# Clean up any existing pinned reports for Administrator
		frappe.defaults.clear_user_default("_crm_pinned_reports", user="Administrator")

		if not frappe.db.exists("Report", TEST_FCRM_REPORT):
			doc = frappe.new_doc("Report")
			doc.name = TEST_FCRM_REPORT
			doc.report_name = TEST_FCRM_REPORT
			doc.report_type = "Script Report"
			doc.ref_doctype = "CRM Lead"
			doc.module = "FCRM"
			doc.is_standard = "No"
			doc.default_print_format = None
			doc.default_letter_head = None
			doc.insert(ignore_permissions=True)

		if not frappe.db.exists("Report", NON_FCRM_TEST_REPORT):
			doc = frappe.new_doc("Report")
			doc.name = NON_FCRM_TEST_REPORT
			doc.report_name = NON_FCRM_TEST_REPORT
			doc.report_type = "Script Report"
			doc.ref_doctype = "CRM Lead"
			doc.module = "CRM"
			doc.is_standard = "No"
			doc.default_print_format = None
			doc.default_letter_head = None
			doc.insert(ignore_permissions=True)

		if not frappe.db.exists("Report", REPORT_BUILDER_TEST_REPORT):
			doc = frappe.new_doc("Report")
			doc.name = REPORT_BUILDER_TEST_REPORT
			doc.report_name = REPORT_BUILDER_TEST_REPORT
			doc.report_type = "Report Builder"
			doc.ref_doctype = "CRM Lead"
			doc.module = "FCRM"
			doc.is_standard = "No"
			doc.default_print_format = None
			doc.default_letter_head = None
			doc.insert(ignore_permissions=True)

		if not frappe.db.exists("Report", PREPARED_TEST_REPORT):
			doc = frappe.new_doc("Report")
			doc.name = PREPARED_TEST_REPORT
			doc.report_name = PREPARED_TEST_REPORT
			doc.report_type = "Script Report"
			doc.prepared_report = 1
			doc.ref_doctype = "CRM Lead"
			doc.module = "FCRM"
			doc.is_standard = "No"
			doc.default_print_format = None
			doc.default_letter_head = None
			doc.insert(ignore_permissions=True)

		if not frappe.db.exists("Report", DISABLED_TEST_REPORT):
			doc = frappe.new_doc("Report")
			doc.name = DISABLED_TEST_REPORT
			doc.report_name = DISABLED_TEST_REPORT
			doc.report_type = "Script Report"
			doc.disabled = 1
			doc.ref_doctype = "CRM Lead"
			doc.module = "FCRM"
			doc.is_standard = "No"
			doc.default_print_format = None
			doc.default_letter_head = None
			doc.insert(ignore_permissions=True)

	def tearDown(self):
		frappe.defaults.clear_user_default("_crm_pinned_reports", user="Administrator")
		for r in (
			TEST_FCRM_REPORT,
			NON_FCRM_TEST_REPORT,
			REPORT_BUILDER_TEST_REPORT,
			PREPARED_TEST_REPORT,
			DISABLED_TEST_REPORT,
		):
			if frappe.db.exists("Report", r):
				frappe.db.delete("Report", {"name": r})

	def test_get_fcrm_reports_includes_fcrm_module_reports(self):
		reports = get_fcrm_reports()
		names = [r["name"] for r in reports]
		self.assertIn(TEST_FCRM_REPORT, names)
		self.assertNotIn(NON_FCRM_TEST_REPORT, names)

	def test_pin_and_unpin_single_report(self):
		pin_report(TEST_FCRM_REPORT, title=TEST_FCRM_REPORT, icon="file-text")
		pinned = get_pinned_reports()
		pinned_names = [r["report"] for r in pinned]
		self.assertIn(TEST_FCRM_REPORT, pinned_names)

		# Duplicate pin should be prevented
		pin_report(TEST_FCRM_REPORT, title=TEST_FCRM_REPORT)
		pinned = get_pinned_reports()
		count = sum(1 for r in pinned if r["report"] == TEST_FCRM_REPORT)
		self.assertEqual(count, 1)

		# Unpin report
		unpin_report(TEST_FCRM_REPORT)
		pinned = get_pinned_reports()
		pinned_names = [r["report"] for r in pinned]
		self.assertNotIn(TEST_FCRM_REPORT, pinned_names)

	def test_pin_multiple_reports(self):
		pin_reports([{"report": TEST_FCRM_REPORT, "title": TEST_FCRM_REPORT}])
		pinned = get_pinned_reports()
		pinned_names = [r["report"] for r in pinned]
		self.assertIn(TEST_FCRM_REPORT, pinned_names)

	def test_non_fcrm_report_pinning_fails(self):
		with self.assertRaises(frappe.PermissionError):
			pin_report(NON_FCRM_TEST_REPORT)

	def test_get_report_data_rejects_non_fcrm_report(self):
		with self.assertRaises(frappe.PermissionError):
			get_report_data(NON_FCRM_TEST_REPORT)

	def test_get_report_meta_rejects_non_fcrm_report(self):
		with self.assertRaises(frappe.PermissionError):
			get_report_meta(NON_FCRM_TEST_REPORT)

	def test_export_report_rejects_non_fcrm_report(self):
		with self.assertRaises(frappe.PermissionError):
			export_report(NON_FCRM_TEST_REPORT)

	def test_get_pinned_reports_excludes_non_fcrm_report(self):
		# If user defaults contain a non-FCRM report, it must be excluded
		frappe.defaults.set_user_default(
			"_crm_pinned_reports",
			json.dumps([{"report": NON_FCRM_TEST_REPORT, "name": NON_FCRM_TEST_REPORT}]),
			user="Administrator",
		)
		pinned = get_pinned_reports()
		pinned_names = [r["report"] for r in pinned]
		self.assertNotIn(NON_FCRM_TEST_REPORT, pinned_names)

	def test_get_pinned_reports_excludes_inaccessible_report(self):
		# Non-existent or deleted reports must be excluded
		frappe.defaults.set_user_default(
			"_crm_pinned_reports",
			json.dumps([{"report": "Non Existent Report", "name": "Non Existent Report"}]),
			user="Administrator",
		)
		pinned = get_pinned_reports()
		pinned_names = [r["report"] for r in pinned]
		self.assertNotIn("Non Existent Report", pinned_names)

	def test_filter_permitted_reports_respects_role_restrictions(self):
		# Standard report without restrictions is permitted
		permitted = _filter_permitted_reports([TEST_FCRM_REPORT])
		self.assertIn(TEST_FCRM_REPORT, permitted)

		# Empty list returns empty set
		self.assertEqual(_filter_permitted_reports([]), set())

	def test_filter_permitted_reports_custom_role_empty_fallback(self):
		from unittest.mock import patch

		# Create a Custom Role record for TEST_FCRM_REPORT with no attached roles
		custom_role = frappe.new_doc("Custom Role")
		custom_role.report = TEST_FCRM_REPORT
		custom_role.insert(ignore_permissions=True)

		saved_user = frappe.session.user
		try:
			frappe.session.user = "test_rep@example.com"
			# Non-admin user with Sales User role should still have access because
			# a Custom Role record with empty roles list falls back to standard roles
			with patch("frappe.get_roles", return_value=["Sales User"]):
				permitted = _filter_permitted_reports([TEST_FCRM_REPORT])
				self.assertIn(TEST_FCRM_REPORT, permitted)

			# When Custom Role defines roles that the user doesn't have, access is denied
			custom_role.append("roles", {"role": "System Manager"})
			custom_role.save(ignore_permissions=True)

			with patch("frappe.get_roles", return_value=["Sales User"]):
				permitted = _filter_permitted_reports([TEST_FCRM_REPORT])
				self.assertNotIn(TEST_FCRM_REPORT, permitted)
		finally:
			frappe.session.user = saved_user
			custom_role.delete(ignore_permissions=True)

	def test_report_builder_and_prepared_reports_are_excluded_from_picker(self):
		reports = get_fcrm_reports()
		names = [r["name"] for r in reports]
		self.assertNotIn(REPORT_BUILDER_TEST_REPORT, names)
		self.assertNotIn(PREPARED_TEST_REPORT, names)

	def test_report_builder_rejected_by_validation(self):
		with self.assertRaises(frappe.ValidationError):
			_validate_fcrm_report(REPORT_BUILDER_TEST_REPORT)

	def test_prepared_report_rejected_by_validation(self):
		with self.assertRaises(frappe.ValidationError):
			_validate_fcrm_report(PREPARED_TEST_REPORT)

	def test_pin_multiple_reports_with_partial_failure_saves_valid_reports(self):
		pin_reports(
			[
				{"report": TEST_FCRM_REPORT, "title": TEST_FCRM_REPORT},
				{"report": NON_FCRM_TEST_REPORT, "title": NON_FCRM_TEST_REPORT},
				{"report": REPORT_BUILDER_TEST_REPORT, "title": REPORT_BUILDER_TEST_REPORT},
			]
		)
		pinned = get_pinned_reports()
		pinned_names = [r["report"] for r in pinned]
		self.assertIn(TEST_FCRM_REPORT, pinned_names)
		self.assertNotIn(NON_FCRM_TEST_REPORT, pinned_names)
		self.assertNotIn(REPORT_BUILDER_TEST_REPORT, pinned_names)

	def test_disabled_report_rejected_by_validation(self):
		with self.assertRaises(frappe.ValidationError):
			_validate_fcrm_report(DISABLED_TEST_REPORT)
