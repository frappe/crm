# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase

from crm.fcrm.doctype.crm_fields_layout.form_layout_conversion import convert_layout


def section(name, fields=(), **keys):
	return {"name": name, "columns": [{"name": f"{name}_column", "fields": list(fields)}], **keys}


def section_names(tabs):
	return [section["name"] for tab in tabs for section in tab["sections"]]


class TestFormLayoutConversion(IntegrationTestCase):
	def test_wraps_a_tabless_layout_in_one_tab(self):
		tabs = convert_layout("CRM Task", "Quick Entry", [section("details_section", ["title"])])

		self.assertEqual([tab["name"] for tab in tabs], ["first_tab"])
		self.assertEqual(section_names(tabs), ["details_section"])

	def test_side_panel_of_lead_and_deal_leads_with_sla_then_lost_reason(self):
		v1 = [
			section("lost_reason_section", ["lost_reason"], label="Lost Reason"),
			section("details_section", ["organization"]),
		]
		for dt in ("CRM Lead", "CRM Deal"):
			tabs = convert_layout(dt, "Side Panel", v1)

			sla, lost, details = tabs[0]["sections"]
			self.assertEqual(sla["name"], "sla_section")
			self.assertEqual(sla["dependsOn"], "sla")
			self.assertEqual(sla["columns"][0]["fields"], ["sla_status", "communication_status"])
			self.assertEqual(lost["name"], "lost_reason_section")
			self.assertEqual(lost["dependsOn"], "lost_reason")
			self.assertEqual(lost["columns"][0]["fields"], ["lost_reason", "lost_notes"])
			self.assertEqual(details["name"], "details_section")

	def test_adds_no_status_sections_outside_lead_and_deal_side_panels(self):
		v1 = [section("details_section", ["organization"])]

		self.assertEqual(
			section_names(convert_layout("CRM Organization", "Side Panel", v1)), ["details_section"]
		)
		self.assertEqual(section_names(convert_layout("CRM Deal", "Data Fields", v1)), ["details_section"])

	def test_removes_the_contacts_section(self):
		v1 = [
			{"label": "Contacts", "name": "contacts_section", "editable": False, "contacts": []},
			section("organization_section", ["organization"]),
		]

		tabs = convert_layout("CRM Deal", "Side Panel", v1)

		self.assertNotIn("contacts_section", section_names(tabs))

	def test_deal_quick_entry_shows_plain_links(self):
		v1 = [
			section("organization_section", ["organization"], hidden=True, editable=False),
			section("organization_details_section", ["organization_name"], editable=False),
			section("contact_section", ["contact"], hidden=True, editable=False),
			section("contact_details_section", ["first_name"], editable=False),
			section("deal_section", ["status"]),
		]

		tabs = convert_layout("CRM Deal", "Quick Entry", v1)

		self.assertEqual(section_names(tabs), ["organization_section", "contact_section", "deal_section"])
		self.assertNotIn("hidden", tabs[0]["sections"][0])
		self.assertNotIn("hidden", tabs[0]["sections"][1])

	def test_removes_a_hidden_section_in_every_other_row(self):
		v1 = [section("person_section", ["email"]), section("organization_section", ["website"], hidden=True)]

		self.assertEqual(section_names(convert_layout("CRM Lead", "Quick Entry", v1)), ["person_section"])
		self.assertEqual(
			section_names(convert_layout("CRM Organization", "Side Panel", v1)), ["person_section"]
		)

	def test_drops_v1_only_keys_from_every_node(self):
		v1 = [
			{
				"name": "details_tab",
				"editingLabel": True,
				"hidden": False,
				"sections": [
					{
						"name": "details_section",
						"label": "Details",
						"editable": True,
						"editingLabel": False,
						"opened": True,
						"columns": [{"name": "details_column", "editable": True, "fields": ["title"]}],
					}
				],
			}
		]

		tabs = convert_layout("CRM Task", "Data Fields", v1)

		self.assertEqual(
			tabs,
			[
				{
					"name": "details_tab",
					"sections": [
						{
							"name": "details_section",
							"label": "Details",
							"opened": True,
							"columns": [{"name": "details_column", "fields": ["title"]}],
						}
					],
				}
			],
		)

	def test_renames_a_name_that_clashes_with_a_field_or_repeats(self):
		v1 = [
			{
				"name": "organization",
				"sections": [
					section("organization", ["organization"]),
					section("details_section", ["website"]),
					{
						"name": "details_section",
						"columns": [{"name": "col", "fields": []}, {"name": "col", "fields": []}],
					},
				],
			}
		]

		tabs = convert_layout("CRM Deal", "Data Fields", v1)

		self.assertEqual(tabs[0]["name"], "organization-2")
		self.assertEqual(section_names(tabs), ["organization-2", "details_section", "details_section-2"])
		self.assertEqual([column["name"] for column in tabs[0]["sections"][2]["columns"]], ["col", "col-2"])
		self.assert_saves_as_form_layout("CRM Deal", "Details", tabs)

	def test_names_an_unnamed_section_without_a_clash(self):
		v1 = [{"label": "Organization", "columns": [{"fields": ["organization"]}]}]

		tabs = convert_layout("CRM Deal", "Side Panel", v1)

		self.assertEqual(section_names(tabs)[-1], "organization-2")
		self.assert_saves_as_form_layout("CRM Deal", "Side Panel", tabs)

	def test_keeps_unknown_fieldnames_and_reads_field_dicts_as_fieldnames(self):
		v1 = [section("details_section", ["title", "no_such_field", {"fieldname": "status"}, {}, ""])]

		tabs = convert_layout("CRM Task", "Quick Entry", v1)

		self.assertEqual(tabs[0]["sections"][0]["columns"][0]["fields"], ["title", "no_such_field", "status"])
		self.assert_saves_as_form_layout("CRM Task", "Quick Entry", tabs)

	def test_leaves_the_v1_tree_untouched(self):
		v1 = [section("organization_section", ["organization"], hidden=True, editable=False)]
		before = frappe.as_json(v1)

		convert_layout("CRM Deal", "Quick Entry", v1)

		self.assertEqual(frappe.as_json(v1), before)

	def assert_saves_as_form_layout(self, dt, type, tabs):
		frappe.db.delete("Form Layout", {"dt": dt, "type": type})
		row = frappe.get_doc(doctype="Form Layout", dt=dt, type=type, layout=frappe.as_json(tabs)).insert()
		self.assertEqual(frappe.parse_json(row.layout), tabs)
