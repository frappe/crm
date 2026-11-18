# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

"""The view files and sidebars CRM ships for its list items.

Both are plain JSON that nothing in CRM runs. A view file the framework cannot use is refused
and logged, never shown, and a sidebar row naming a view that is gone opens the plain list --
each is a quietly smaller product, which is why they are asserted here.
"""

import glob
import json
import os

import frappe
from frappe.desk.doctype.doctype_view.app_views import app_plain_settings, app_views
from frappe.tests import IntegrationTestCase

SIDEBARS = {
	"doctype_crm_lead": "CRM Lead",
	"doctype_crm_deal": "CRM Deal",
	"doctype_crm_task": "CRM Task",
	"doctype_fcrm_note": "FCRM Note",
	"doctype_crm_call_log": "CRM Call Log",
}


class TestCRMViewSidebars(IntegrationTestCase):
	def test_every_view_file_is_accepted(self):
		"""`app_views` drops a file it refuses, so a file missing from it is a broken file."""
		for doctype in SIDEBARS.values():
			accepted = set(app_views(doctype))
			for key in view_files(doctype):
				if key == "list":
					self.assertIsNotNone(app_plain_settings(doctype, "list"), doctype)
				else:
					self.assertIn(key, accepted, f"{doctype}/{key}")

	def test_every_view_row_opens_a_view_that_exists(self):
		for address, doctype in SIDEBARS.items():
			views = app_views(doctype)
			rows = frappe.get_all(
				"Navigation Item",
				filters={"parenttype": "Sidebar", "parent": address, "item_type": "View"},
				fields=["key", "link_to", "payload"],
			)
			self.assertTrue(rows, address)
			for row in rows:
				view = json.loads(row.payload)["view"]
				self.assertEqual(row.link_to, doctype, f"{address}/{row.key}")
				if view == "list":
					self.assertIsNotNone(app_plain_settings(doctype, "list"), f"{address}/{row.key}")
				else:
					self.assertIn(view, views, f"{address}/{row.key}")

	def test_every_view_file_has_a_sidebar_row(self):
		for address, doctype in SIDEBARS.items():
			payloads = frappe.get_all(
				"Navigation Item",
				filters={"parenttype": "Sidebar", "parent": address, "item_type": "View"},
				pluck="payload",
			)
			opened = {json.loads(payload)["view"] for payload in payloads}
			files = set(view_files(doctype)) - {"list"}
			self.assertTrue(files, doctype)
			self.assertLessEqual(files, opened, doctype)

	def test_every_filter_value_is_one_the_field_accepts(self):
		"""A list view has no settings check for filter values, so a renamed status ships as an empty view."""
		for doctype in SIDEBARS.values():
			meta = frappe.get_meta(doctype)
			for key, settings in view_files(doctype).items():
				for fieldname, operator, value in settings.get("filters", []):
					if operator not in ("=", "in", "not in"):
						continue
					field = meta.get_field(fieldname)
					values = value if isinstance(value, list) else [value]
					for one in values:
						self.assertTrue(accepts(field, one), f"{doctype}/{key}: {fieldname} {one!r}")

	def test_every_field_a_view_names_is_on_its_doctype(self):
		for doctype in SIDEBARS.values():
			# `_assign` is a column of the table the framework adds, not a field of the doctype.
			columns = {*frappe.get_meta(doctype).get_valid_columns(), "_assign"}
			for key, settings in view_files(doctype).items():
				for fieldname in fields_named(settings):
					self.assertIn(fieldname, columns, f"{doctype}/{key}")


def view_files(doctype: str) -> dict[str, dict]:
	"""`{key: settings}` of the files under the doctype's `frontend/views`, plain list file included."""
	folder = os.path.join(
		frappe.get_app_path("crm"), "fcrm", "doctype", frappe.scrub(doctype), "frontend", "views"
	)
	files = {}
	for path in glob.glob(os.path.join(folder, "*.json")):
		with open(path) as file:
			data = json.load(file)
		files[os.path.basename(path).removesuffix(".json")] = data.get("settings", data)
	return files


def accepts(field, value) -> bool:
	"""Select options and Link targets are checked; any other field takes any value."""
	if field and field.fieldtype == "Select":
		return value in (field.options or "").split("\n")
	if field and field.fieldtype == "Link":
		return bool(frappe.db.exists(field.options, value))
	return True


def fields_named(settings: dict) -> list[str]:
	named = [column["fieldname"] for column in settings.get("columns", [])]
	named += [sort["fieldname"] for sort in settings.get("sort", [])]
	named += [filter_[0] for filter_ in settings.get("filters", [])]
	named += [settings[key] for key in ("title_field", "body_field") if key in settings]
	return named
