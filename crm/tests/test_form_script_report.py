# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

"""The CRM Form Script list as the report: each row's v1 shape, status and calls (frappe/frappe#45967)."""

import os

import frappe
from frappe.shell.navigation import resolve_navigation
from frappe.tests import IntegrationTestCase
from frappe.utils import get_datetime

from crm.fcrm.doctype.crm_form_script.crm_form_script import (
	NO_COUNTERPART,
	REWRITE,
	REWRITE_WITH_GAPS,
	UNKNOWN_SHAPE,
	refresh_analysis,
)
from crm.patches.v1_0.analyse_form_scripts import execute as analyse_every_row
from crm.tests.test_navigation import make_desk_user

FIXTURES = os.path.join(os.path.dirname(__file__), "form_scripts")


def fixture(name: str) -> str:
	with open(os.path.join(FIXTURES, name)) as f:
		return f.read()


def make_script(name: str, script: str, dt: str = "CRM Lead", view: str = "Form"):
	return frappe.get_doc(
		{"doctype": "CRM Form Script", "name": name, "dt": dt, "view": view, "script": script}
	).insert(ignore_permissions=True)


class TestFormScriptReport(IntegrationTestCase):
	def test_each_fixture_saves_with_its_shape_and_status(self):
		for name, dt, view, shape, status in (
			("class_crm_deal.js", "CRM Deal", "Form", "Class-based", REWRITE),
			("setup_form_crm_lead.js", "CRM Lead", "Form", "setupForm", REWRITE),
			("setup_list_crm_lead.js", "CRM Lead", "List", "setupList", REWRITE_WITH_GAPS),
		):
			doc = make_script(f"Test 45967 {name}", fixture(name), dt, view)

			self.assertEqual((doc.v1_shape, doc.migration_status), (shape, status), name)
			self.assertTrue(doc.v1_calls, name)

	def test_each_call_keeps_its_line_verb_anchor_and_gap(self):
		doc = make_script(
			"Test 45967 calls",
			"function setupForm({ doc }) {\n  doc.status = 'Open'\n  toast.info('x')\n  return {}\n}",
		)

		calls = {call.catalog_key: call for call in doc.v1_calls}
		toast = calls["toast-info"]
		self.assertEqual((toast.line, toast.v1_call, toast.verb), (3, "toast.info", NO_COUNTERPART))
		self.assertEqual(toast.gap, "https://github.com/frappe/frappe/issues/46005")
		self.assertEqual(doc.migration_status, REWRITE_WITH_GAPS)
		self.assertTrue(all(call.verb for call in doc.v1_calls))

	def test_a_script_of_no_known_shape_is_unknown(self):
		doc = make_script("Test 45967 unknown", "console.log('hello')")

		self.assertEqual((doc.v1_shape, doc.migration_status), ("Unknown", UNKNOWN_SHAPE))

	def test_saving_again_recomputes_the_calls(self):
		doc = make_script("Test 45967 resave", fixture("setup_form_crm_lead.js"))

		doc.script = "console.log('gone')"
		doc.save(ignore_permissions=True)
		doc.reload()

		self.assertEqual((doc.v1_shape, doc.v1_calls), ("Unknown", []))
		self.assertFalse(frappe.get_all("CRM Form Script Call", filters={"parent": doc.name}))

	def test_a_script_written_directly_is_analysed_without_a_new_modified(self):
		"""The writers that `set_value` a standard row's script, and the patch, go through this."""
		doc = make_script("Test 45967 direct", "console.log('x')")
		modified = doc.modified

		frappe.db.set_value(
			"CRM Form Script", doc.name, "script", fixture("setup_form_crm_lead.js"), update_modified=False
		)
		refresh_analysis(doc.name)
		doc.reload()

		self.assertEqual((doc.v1_shape, doc.migration_status), ("setupForm", REWRITE))
		self.assertTrue(doc.v1_calls)
		self.assertEqual(get_datetime(doc.modified), get_datetime(modified))

	def test_the_patch_fills_every_row(self):
		doc = make_script("Test 45967 patch", fixture("class_crm_deal.js"), "CRM Deal")
		frappe.db.set_value("CRM Form Script", doc.name, {"v1_shape": None, "migration_status": None})
		frappe.db.delete("CRM Form Script Call", {"parent": doc.name})

		analyse_every_row()
		doc.reload()

		self.assertEqual((doc.v1_shape, doc.migration_status), ("Class-based", REWRITE))
		self.assertTrue(doc.v1_calls)
		for name in frappe.get_all("CRM Form Script", pluck="name"):
			self.assertTrue(frappe.db.get_value("CRM Form Script", name, "migration_status"), name)

	def test_the_standard_scripts_need_only_a_rewrite(self):
		for name in frappe.get_all("CRM Form Script", filters={"is_standard": 1}, pluck="name"):
			refresh_analysis(name)
			self.assertEqual(frappe.db.get_value("CRM Form Script", name, "migration_status"), REWRITE, name)


class TestFormScriptReportPermissions(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.sales_user = make_desk_user("crm.form.script.report.user@example.com")
		cls.sales_manager = make_desk_user("crm.form.script.report.manager@example.com", "Sales Manager")
		cls.system_manager = make_desk_user("crm.form.script.report.admin@example.com", "System Manager")
		cls.script = make_script("Test 45967 permissions", fixture("setup_list_crm_lead.js"), view="List")

	def setUp(self):
		self.addCleanup(frappe.set_user, "Administrator")

	def test_sales_roles_read_the_report_but_cannot_change_it(self):
		for user in (self.sales_user, self.sales_manager):
			frappe.set_user(user)
			row = frappe.get_list(
				"CRM Form Script",
				filters={"name": self.script.name},
				fields=["v1_shape", "migration_status"],
			)
			self.assertEqual(row, [{"v1_shape": "setupList", "migration_status": REWRITE_WITH_GAPS}], user)
			self.assertTrue(frappe.get_doc("CRM Form Script", self.script.name).v1_calls, user)
			self.assertFalse(frappe.has_permission("CRM Form Script", "write", user=user), user)

	def test_only_a_system_manager_is_offered_the_setup_row(self):
		for user, offered in (
			(self.system_manager, True),
			(self.sales_manager, False),
			(self.sales_user, False),
		):
			frappe.set_user(user)
			rows = resolve_navigation("crm")["sidebars"].get("module_def_fcrm", [])
			self.assertEqual("form-scripts" in [row["key"] for row in rows], offered, user)
