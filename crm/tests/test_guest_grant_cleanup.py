# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe
from frappe.permissions import add_permission
from frappe.tests import IntegrationTestCase

from crm.api.form import GUEST_SELECT_REFUSED
from crm.patches.v1_0 import remove_guest_grants_on_refused_doctypes as patch

KEPT_DOCTYPE = "CRM Lead Source"


class TestGuestGrantCleanup(IntegrationTestCase):
	def tearDown(self):
		frappe.db.rollback()
		for doctype in (*GUEST_SELECT_REFUSED, KEPT_DOCTYPE):
			frappe.clear_cache(doctype=doctype)

	def test_removes_guest_rows_on_refused_doctypes_only(self):
		for doctype in (*GUEST_SELECT_REFUSED, KEPT_DOCTYPE):
			add_permission(doctype, "Guest", 0, ptype="select")
			frappe.clear_cache(doctype=doctype)
			self.assertTrue(frappe.has_permission(doctype, ptype="select", user="Guest"))
		other_rows = {doctype: self.custom_perms(doctype, "!=") for doctype in GUEST_SELECT_REFUSED}

		patch.execute()

		for doctype in GUEST_SELECT_REFUSED:
			with self.subTest(doctype=doctype):
				self.assertEqual(self.custom_perms(doctype, "="), [])
				self.assertEqual(self.custom_perms(doctype, "!="), other_rows[doctype])
				self.assertFalse(frappe.has_permission(doctype, ptype="select", user="Guest"))
		self.assertTrue(self.custom_perms(KEPT_DOCTYPE, "="))
		self.assertTrue(frappe.has_permission(KEPT_DOCTYPE, ptype="select", user="Guest"))

	def test_runs_again_without_guest_rows(self):
		patch.execute()
		patch.execute()

		for doctype in GUEST_SELECT_REFUSED:
			self.assertEqual(self.custom_perms(doctype, "="), [])

	def custom_perms(self, doctype, role_operator):
		return frappe.get_all(
			"Custom DocPerm",
			filters={"parent": doctype, "role": [role_operator, "Guest"]},
			pluck="name",
			order_by="name",
		)
