# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import json

import frappe
from frappe.tests import UnitTestCase

from crm.api.activities import get_field_change_activities

FIELDS = {
	"probability": {"label": "Probability"},
	"status": {"label": "Status"},
	"email": {"label": "Email"},
	"sla": {"label": "SLA"},
}


def make_version(changed):
	return frappe._dict(
		data=json.dumps({"changed": changed}),
		creation="2026-10-29 10:59:37",
		owner="agent@example.com",
	)


class TestFieldChangeActivities(UnitTestCase):
	def test_every_changed_field_is_reported(self):
		version = make_version([["probability", 25, 100], ["status", "Demo/Making", "Won"]])

		activities = get_field_change_activities(version, FIELDS, [], is_lead=False)

		self.assertEqual([a["data"]["field"] for a in activities], ["probability", "status"])
		self.assertEqual(activities[1]["data"]["old_value"], "Demo/Making")
		self.assertEqual(activities[1]["data"]["value"], "Won")

	def test_added_and_removed(self):
		version = make_version([["email", None, "a@b.com"], ["status", "Open", None]])

		added, removed = get_field_change_activities(version, FIELDS, [], is_lead=True)

		self.assertEqual((added["activity_type"], added["data"]["value"]), ("added", "a@b.com"))
		self.assertEqual((removed["activity_type"], removed["data"]["value"]), ("removed", "Open"))
		self.assertNotIn("old_value", added["data"])

	def test_skips_avoided_unknown_and_empty_changes(self):
		version = make_version([["sla", "A", "B"], ["unknown", 1, 2], ["email", "", None]])

		self.assertEqual(get_field_change_activities(version, FIELDS, ["sla"], is_lead=False), [])
