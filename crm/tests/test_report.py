# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import json
from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from crm.api.report import (
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
			# role rows a test added, so they don't restrict the next test's report
			frappe.db.delete("Has Role", {"parenttype": "Report", "parent": r})

	def test_get_fcrm_reports_includes_fcrm_module_reports(self):
		reports = get_fcrm_reports()
		names = [r["name"] for r in reports]
		self.assertIn(TEST_FCRM_REPORT, names)
		self.assertNotIn(NON_FCRM_TEST_REPORT, names)

	def test_pin_and_unpin_single_report(self):
		pin_report(TEST_FCRM_REPORT, icon="file-text")
		pinned = get_pinned_reports()
		pinned_names = [r["report"] for r in pinned]
		self.assertIn(TEST_FCRM_REPORT, pinned_names)

		# Duplicate pin should be prevented
		pin_report(TEST_FCRM_REPORT)
		pinned = get_pinned_reports()
		count = sum(1 for r in pinned if r["report"] == TEST_FCRM_REPORT)
		self.assertEqual(count, 1)

		# Unpin report
		unpin_report(TEST_FCRM_REPORT)
		pinned = get_pinned_reports()
		pinned_names = [r["report"] for r in pinned]
		self.assertNotIn(TEST_FCRM_REPORT, pinned_names)

	def test_pin_multiple_reports(self):
		result = pin_reports([{"report": TEST_FCRM_REPORT}])
		self.assertEqual(result, {"added": [TEST_FCRM_REPORT], "skipped": []})
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
			json.dumps([{"report": NON_FCRM_TEST_REPORT}]),
			user="Administrator",
		)
		pinned = get_pinned_reports()
		pinned_names = [r["report"] for r in pinned]
		self.assertNotIn(NON_FCRM_TEST_REPORT, pinned_names)

	def test_get_pinned_reports_excludes_inaccessible_report(self):
		# Non-existent or deleted reports must be excluded
		frappe.defaults.set_user_default(
			"_crm_pinned_reports",
			json.dumps([{"report": "Non Existent Report"}]),
			user="Administrator",
		)
		pinned = get_pinned_reports()
		pinned_names = [r["report"] for r in pinned]
		self.assertNotIn("Non Existent Report", pinned_names)

	def test_picker_and_pinning_agree_for_system_manager_without_report_role(self):
		# System Manager gets no bypass in core Report.is_permitted(), so the picker
		# must not offer a report that pinning would then refuse
		user = make_user("sysmgr@report.test", ["System Manager", "Sales User"])
		# new reports get roles from their doctype's permissions; allow only Sales Manager
		report = frappe.get_doc("Report", TEST_FCRM_REPORT)
		report.set("roles", [{"role": "Sales Manager"}])
		report.save(ignore_permissions=True)

		frappe.set_user(user.name)
		try:
			self.assertNotIn(TEST_FCRM_REPORT, [r["name"] for r in get_fcrm_reports()])
			result = pin_reports([{"report": TEST_FCRM_REPORT}])
		finally:
			frappe.set_user("Administrator")

		self.assertEqual(result["added"], [])
		self.assertEqual([s["report"] for s in result["skipped"]], [TEST_FCRM_REPORT])
		self.assertTrue(result["skipped"][0]["reason"])

	def test_custom_role_overrides_report_roles(self):
		user = make_user("salesrep@report.test", ["Sales User"])
		custom_role = frappe.new_doc("Custom Role")
		custom_role.report = TEST_FCRM_REPORT
		custom_role.append("roles", {"role": "Sales Manager"})
		custom_role.insert(ignore_permissions=True)

		frappe.set_user(user.name)
		try:
			self.assertNotIn(TEST_FCRM_REPORT, [r["name"] for r in get_fcrm_reports()])
			with self.assertRaises(frappe.PermissionError):
				pin_report(TEST_FCRM_REPORT)
		finally:
			frappe.set_user("Administrator")
			custom_role.delete(ignore_permissions=True)

	def test_pinned_title_follows_report_name(self):
		pin_report(TEST_FCRM_REPORT)
		frappe.db.set_value("Report", TEST_FCRM_REPORT, "report_name", "Renamed Report")
		(pinned,) = get_pinned_reports()
		self.assertEqual(pinned["title"], "Renamed Report")

	def test_total_row_is_returned_separately(self):
		frappe.db.set_value("Report", TEST_FCRM_REPORT, "add_total_row", 1)
		with patch_report_result(
			["Deal:Link/CRM Deal:120", "Value:Currency:100"],
			[["CRM-DEAL-1", 100], ["CRM-DEAL-2", 50]],
		):
			data = get_report_data(TEST_FCRM_REPORT)

		self.assertEqual([r["deal"] for r in data["rows"]], ["CRM-DEAL-1", "CRM-DEAL-2"])
		self.assertEqual(data["total_row"]["deal"], "Total")
		self.assertEqual(data["total_row"]["value"], 150)

	def test_column_widths_are_css_lengths(self):
		with patch_report_result(
			["Deal:Link/CRM Deal:120", {"label": "Value", "fieldname": "value", "width": 90}],
			[["CRM-DEAL-1", 100]],
		):
			columns = get_report_data(TEST_FCRM_REPORT)["columns"]

		self.assertEqual([c["width"] for c in columns], ["120px", "90px"])

	def test_export_without_columns_raises_instead_of_returning_a_page(self):
		with patch_report_result([], []), self.assertRaises(frappe.ValidationError):
			export_report(TEST_FCRM_REPORT, file_format_type="CSV")

	def test_export_uses_labelled_applied_filters(self):
		captured = {}

		def fake_build_xlsx_data(data, *args, **kwargs):
			captured["applied_filters"] = dict(data.applied_filters)
			return [["x"]], [10], None

		with (
			patch_report_result(["Deal:Data:100"], [["CRM-DEAL-1"]]),
			patch("frappe.desk.query_report.build_xlsx_data", fake_build_xlsx_data),
		):
			export_report(
				TEST_FCRM_REPORT,
				file_format_type="CSV",
				filters={"status": "Open"},
				applied_filters={"Status": "Open"},
			)

		self.assertEqual(captured["applied_filters"], {"Status": "Open"})

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
		result = pin_reports(
			[
				{"report": TEST_FCRM_REPORT},
				{"report": NON_FCRM_TEST_REPORT},
				{"report": REPORT_BUILDER_TEST_REPORT},
			]
		)
		self.assertEqual(result["added"], [TEST_FCRM_REPORT])
		self.assertEqual(
			{s["report"] for s in result["skipped"]}, {NON_FCRM_TEST_REPORT, REPORT_BUILDER_TEST_REPORT}
		)
		pinned = get_pinned_reports()
		pinned_names = [r["report"] for r in pinned]
		self.assertIn(TEST_FCRM_REPORT, pinned_names)
		self.assertNotIn(NON_FCRM_TEST_REPORT, pinned_names)
		self.assertNotIn(REPORT_BUILDER_TEST_REPORT, pinned_names)

	def test_disabled_report_rejected_by_validation(self):
		with self.assertRaises(frappe.ValidationError):
			_validate_fcrm_report(DISABLED_TEST_REPORT)


def patch_report_result(columns, rows):
	"""Stand in for the report's own script; everything above it (run, total row) is real."""
	return patch("frappe.desk.query_report.get_report_result", return_value=[columns, rows])


def make_user(email, roles):
	if not frappe.db.exists("User", email):
		frappe.get_doc(
			{"doctype": "User", "email": email, "first_name": email.split("@")[0], "send_welcome_email": 0}
		).insert(ignore_permissions=True)
	user = frappe.get_doc("User", email)
	user.add_roles(*roles)
	return user
