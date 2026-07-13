# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

from crm.fcrm.doctype.crm_view_settings.crm_view_settings import reconcile_kanban_columns
from frappe.tests import UnitTestCase


class TestCRMViewSettings(UnitTestCase):
	def test_reconcile_kanban_columns_removes_stale_and_preserves_settings(self):
		existing = [
			{"name": "Contacted", "color": "blue", "order": ["LEAD-1"]},
			{"name": "Old Status", "color": "red"},
			{"name": "Qualified", "delete": True},
		]
		current = [{"name": "New"}, {"name": "Contacted"}, {"name": "Qualified"}]

		columns = reconcile_kanban_columns(existing, current)

		self.assertEqual(
			columns,
			[
				{"name": "Contacted", "color": "blue", "order": ["LEAD-1"]},
				{"name": "Qualified", "delete": True},
				{"name": "New"},
			],
		)

	def test_reconcile_kanban_columns_can_hide_new_columns(self):
		columns = reconcile_kanban_columns(
			[{"name": "New"}],
			[{"name": "New"}, {"name": "Qualified"}],
			hide_new=True,
		)

		self.assertEqual(columns, [{"name": "New"}, {"name": "Qualified", "delete": True}])
