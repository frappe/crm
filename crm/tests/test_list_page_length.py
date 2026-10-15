import json

import frappe
from frappe.tests import IntegrationTestCase

from crm.api.doc import get_data


def lead_list(**kwargs):
	params = {
		"doctype": "CRM Lead",
		"filters": {},
		"order_by": "modified desc",
		"page_length": 20,
		"page_length_count": 20,
		"view": {"view_type": "list"},
	}
	params.update(kwargs)
	return get_data(**params)


class TestListPageLength(IntegrationTestCase):
	"""The response must echo the top-level `page_length` /
	`page_length_count` that were requested, not a kanban column's (see #2835)."""

	def setUp(self):
		frappe.set_user("Administrator")

	def tearDown(self):
		frappe.db.rollback()

	def test_list_response_echoes_requested_page_length(self):
		result = lead_list(page_length=40, page_length_count=20)

		self.assertEqual(result["page_length"], 40)
		self.assertEqual(result["page_length_count"], 20)

	def test_kanban_column_page_length_does_not_leak_into_response(self):
		"""'Load More' on a kanban column bumps that column's own page_length;
		the top-level value in the response must not pick it up, otherwise
		switching to list / group_by view fetches the column's page size."""
		statuses = frappe.get_all("CRM Lead Status", pluck="name", order_by="position asc")
		self.assertGreater(len(statuses), 0)

		kanban_columns = [{"name": status} for status in statuses]
		kanban_columns[-1]["page_length"] = 40

		result = lead_list(
			column_field="status",
			title_field="first_name",
			kanban_columns=json.dumps(kanban_columns),
			kanban_fields=json.dumps(["name"]),
			view={"view_type": "kanban"},
		)

		self.assertEqual(result["page_length"], 20)
		self.assertEqual(result["page_length_count"], 20)
