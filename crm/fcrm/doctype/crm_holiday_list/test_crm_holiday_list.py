# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import json

import frappe
from frappe.tests import IntegrationTestCase

RECURRING = [{"day": "Sunday", "repetition": {"all": True}}]


def make_holiday_list(**kwargs):
	return frappe.get_doc(
		{
			"doctype": "CRM Holiday List",
			"holiday_list_name": "_Test CRM Holiday List",
			"from_date": "2026-01-01",
			"to_date": "2026-12-31",
			**kwargs,
		}
	)


class TestCRMHolidayList(IntegrationTestCase):
	def tearDown(self):
		frappe.db.rollback()

	def test_saves_description_and_recurring_holidays(self):
		doc = make_holiday_list(
			description="Office closures",
			recurring_holidays=json.dumps(RECURRING),
			holidays=[
				{"date": "2026-01-04", "description": "Sunday", "weekly_off": 1},
				{"date": "2026-01-26", "description": "Republic Day"},
			],
		).insert()

		doc.reload()
		self.assertEqual(doc.description, "Office closures")
		self.assertEqual(json.loads(doc.recurring_holidays), RECURRING)
		self.assertEqual(doc.total_holidays, 2)

	def test_rejects_reversed_range(self):
		doc = make_holiday_list(from_date="2026-12-31", to_date="2026-01-01")
		self.assertRaises(frappe.ValidationError, doc.insert)

	def test_rejects_holiday_outside_range(self):
		doc = make_holiday_list(holidays=[{"date": "2027-01-01", "description": "New Year"}])
		self.assertRaises(frappe.ValidationError, doc.insert)
