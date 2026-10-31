# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase

from crm.fcrm.doctype.crm_fields_layout.form_layout_conversion import convert_layout
from crm.fcrm.doctype.crm_fields_layout.form_layout_mirror import FORM_LAYOUT_TYPES, MIRRORED_DOCTYPES
from crm.fcrm.doctype.utils import add_or_remove_lost_reason_section_in_sidepanel
from crm.patches.v1_0 import mirror_fields_layouts_to_form_layout

TASK_PANEL = [
	{"name": "details_section", "columns": [{"name": "details_column", "fields": ["title", "status"]}]}
]


def default_rows(dt, type):
	return frappe.get_all(
		"Form Layout",
		filters={"dt": dt, "type": type, "condition": ("is", "not set")},
		fields=["name", "layout", "modified"],
	)


def save_v1_layout(dt, type, layout):
	name = f"{dt}-{type}"
	if frappe.db.exists("CRM Fields Layout", name):
		doc = frappe.get_doc("CRM Fields Layout", name)
	else:
		doc = frappe.new_doc("CRM Fields Layout", dt=dt, type=type)
	doc.layout = frappe.as_json(layout)
	doc.save()
	return doc


class TestCRMFieldsLayoutMirror(IntegrationTestCase):
	def setUp(self):
		frappe.db.delete("CRM Fields Layout", {"dt": "CRM Task", "type": "Side Panel"})
		frappe.db.delete("Form Layout", {"dt": "CRM Task", "type": "Side Panel"})

	def test_insert_writes_the_converted_default_row(self):
		save_v1_layout("CRM Task", "Side Panel", TASK_PANEL)

		(row,) = default_rows("CRM Task", "Side Panel")
		self.assertEqual(frappe.parse_json(row.layout), convert_layout("CRM Task", "Side Panel", TASK_PANEL))

	def test_data_fields_mirror_to_details(self):
		save_v1_layout("CRM Task", "Data Fields", TASK_PANEL)

		self.assertEqual(len(default_rows("CRM Task", "Details")), 1)

	def test_update_rewrites_the_default_row(self):
		save_v1_layout("CRM Task", "Side Panel", TASK_PANEL)
		changed = [{**TASK_PANEL[0], "label": "Task"}]

		save_v1_layout("CRM Task", "Side Panel", changed)

		(row,) = default_rows("CRM Task", "Side Panel")
		self.assertEqual(frappe.parse_json(row.layout)[0]["sections"][0]["label"], "Task")

	def test_an_unchanged_conversion_skips_the_save(self):
		save_v1_layout("CRM Task", "Side Panel", TASK_PANEL)
		(before,) = default_rows("CRM Task", "Side Panel")

		save_v1_layout("CRM Task", "Side Panel", [{**TASK_PANEL[0], "editingLabel": True}])

		(after,) = default_rows("CRM Task", "Side Panel")
		self.assertEqual(after.modified, before.modified)

	def test_v1_lost_reason_rewrite_does_not_write_form_layout(self):
		(before,) = default_rows("CRM Deal", "Side Panel")
		lost = frappe.db.get_value("CRM Deal Status", {"type": "Lost"})
		open_ = frappe.db.get_value("CRM Deal Status", {"type": ("!=", "Lost")})

		for status in (lost, open_):
			add_or_remove_lost_reason_section_in_sidepanel(frappe._dict(doctype="CRM Deal", status=status))

		v1 = frappe.get_doc("CRM Fields Layout", "CRM Deal-Side Panel")
		self.assertGreater(v1.modified, before.modified)
		(after,) = default_rows("CRM Deal", "Side Panel")
		self.assertEqual(after.modified, before.modified)

	def test_a_desk_v2_omitted_list_is_lost_at_the_next_v1_save(self):
		save_v1_layout("CRM Task", "Side Panel", TASK_PANEL)
		(row,) = default_rows("CRM Task", "Side Panel")
		frappe.db.set_value("Form Layout", row.name, "omitted", '["status"]')

		save_v1_layout("CRM Task", "Side Panel", TASK_PANEL)

		self.assertIsNone(frappe.db.get_value("Form Layout", row.name, "omitted"))

	def test_moving_a_v1_row_to_another_type_moves_its_mirror(self):
		doc = save_v1_layout("CRM Task", "Side Panel", TASK_PANEL)
		frappe.db.delete("Form Layout", {"dt": "CRM Task", "type": "Details"})

		doc.type = "Data Fields"
		doc.save()

		self.assertEqual(default_rows("CRM Task", "Side Panel"), [])
		self.assertEqual(len(default_rows("CRM Task", "Details")), 1)

	def test_trash_deletes_the_default_row(self):
		save_v1_layout("CRM Task", "Side Panel", TASK_PANEL).delete()

		self.assertEqual(default_rows("CRM Task", "Side Panel"), [])

	def test_an_emptied_v1_layout_deletes_the_default_row(self):
		save_v1_layout("CRM Task", "Side Panel", TASK_PANEL)

		save_v1_layout("CRM Task", "Side Panel", [])

		self.assertEqual(default_rows("CRM Task", "Side Panel"), [])

	def test_an_emptied_deal_side_panel_keeps_the_sla_and_lost_reason_sections(self):
		save_v1_layout("CRM Deal", "Side Panel", [])

		(row,) = default_rows("CRM Deal", "Side Panel")
		names = [section["name"] for section in frappe.parse_json(row.layout)[0]["sections"]]
		self.assertEqual(names, ["sla_section", "lost_reason_section"])

	def test_a_malformed_v1_tree_still_mirrors(self):
		save_v1_layout(
			"CRM Task", "Side Panel", [{"name": "details_section", "columns": 3, "fields": ["title"]}]
		)

		(row,) = default_rows("CRM Task", "Side Panel")
		self.assertEqual(frappe.parse_json(row.layout)[0]["sections"][0]["columns"], [])

	def test_leaves_rows_with_a_condition_alone(self):
		conditioned = frappe.get_doc(
			doctype="Form Layout",
			dt="CRM Task",
			type="Side Panel",
			condition="doc.status == 'Done'",
			layout=frappe.as_json(TASK_PANEL),
		).insert()

		save_v1_layout("CRM Task", "Side Panel", [{**TASK_PANEL[0], "label": "Task"}]).delete()

		conditioned.reload()
		self.assertEqual(frappe.parse_json(conditioned.layout), TASK_PANEL)

	def test_skips_foreign_doctypes_and_unmoved_types(self):
		frappe.db.delete("Form Layout", {"dt": ("in", ("Contact", "Address"))})
		for dt, type in (("Contact", "Quick Entry"), ("Contact", "Side Panel"), ("Address", "Quick Entry")):
			save_v1_layout(dt, type, TASK_PANEL)
		save_v1_layout("CRM Deal", "Grid Row", TASK_PANEL)
		save_v1_layout("CRM Deal", "Required Fields", TASK_PANEL)

		self.assertFalse(frappe.db.exists("Form Layout", {"dt": ("in", ("Contact", "Address"))}))
		types = {row.type for row in frappe.get_all("Form Layout", {"dt": "CRM Deal"}, ["type"])}
		self.assertEqual(types, {"Quick Entry", "Side Panel", "Details"})

	def test_forecasting_reaches_form_layout(self):
		settings = frappe.get_single("FCRM Settings")
		settings.enable_forecasting = 1
		settings.save()

		(panel,) = default_rows("CRM Deal", "Side Panel")
		self.assertIn("forecasted_sales_section", panel.layout)

		settings.enable_forecasting = 0
		settings.save()

		(panel,) = default_rows("CRM Deal", "Side Panel")
		self.assertNotIn("forecasted_sales_section", panel.layout)


class TestMirrorFieldsLayoutsPatch(IntegrationTestCase):
	def test_mirrors_every_existing_layout_of_a_crm_doctype(self):
		frappe.db.delete("Form Layout")

		mirror_fields_layouts_to_form_layout.execute()

		rows = {(row.dt, row.type) for row in frappe.get_all("Form Layout", fields=["dt", "type"])}
		expected = {
			(dt, FORM_LAYOUT_TYPES[type])
			for dt, type in frappe.get_all("CRM Fields Layout", fields=["dt", "type"], as_list=True)
			if dt in MIRRORED_DOCTYPES and type in FORM_LAYOUT_TYPES
		}
		self.assertEqual(rows, expected)
		self.assertIn(("CRM Deal", "Details"), rows)

	def test_running_twice_changes_nothing(self):
		mirror_fields_layouts_to_form_layout.execute()
		before = frappe.get_all("Form Layout", fields=["name", "modified"], order_by="name")

		mirror_fields_layouts_to_form_layout.execute()

		self.assertEqual(frappe.get_all("Form Layout", fields=["name", "modified"], order_by="name"), before)
