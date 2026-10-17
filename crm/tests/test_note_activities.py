# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

from frappe.tests import UnitTestCase

from crm.api.activities import group_note_activities, ungroup_note_activities


def note(name, owner="a@example.com"):
	return {"name": name, "activity_type": "note", "owner": owner}


class TestNoteActivities(UnitTestCase):
	def test_regrouping_lead_notes_does_not_nest(self):
		lead_activities = group_note_activities([note("lead-2"), note("lead-1")])
		combined = [note("deal-1"), *ungroup_note_activities(lead_activities)]

		grouped = group_note_activities(combined)

		self.assertEqual(len(grouped), 1)
		self.assertEqual([n["name"] for n in grouped[0]["other_notes"]], ["lead-2", "lead-1"])
		self.assertNotIn("other_notes", grouped[0]["other_notes"][0])
