import json

import frappe
from frappe.tests import IntegrationTestCase

from crm.api.doc import get_data


def contact_list(**kwargs):
	return get_data(
		doctype="Contact",
		filters={},
		order_by="modified desc",
		page_length=1,
		view={"view_type": "list"},
		**kwargs,
	)


class TestListViewColumns(IntegrationTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		frappe.db.delete("CRM View Settings", {"dt": "Contact", "user": "Administrator"})

	def tearDown(self):
		frappe.db.rollback()

	def test_default_columns_keep_hidden_fields_chosen_by_controller(self):
		"""Contact.full_name is hidden in the framework schema, but the CRM
		controller picks it as the Name column so it must stay."""
		self.assertTrue(frappe.get_meta("Contact").get_field("full_name").hidden)

		result = contact_list()
		keys = [column["key"] for column in result["columns"]]

		self.assertTrue(result["is_default"])
		self.assertEqual(keys[0], "full_name")
		self.assertEqual(keys, ["full_name", "email_id", "mobile_no", "company_name", "modified"])

	def test_custom_columns_drop_hidden_fields_not_in_defaults(self):
		"""A hidden field the controller did not choose is still removed, and the
		column right after it is still processed."""
		columns = json.dumps(
			[
				{"label": "Image", "type": "Attach Image", "key": "image", "width": "8rem"},
				{"label": "Email", "type": "Data", "key": "email_id", "width": "12rem"},
			]
		)

		result = contact_list(columns=columns, rows=json.dumps(["name"]))
		keys = [column["key"] for column in result["columns"]]

		self.assertEqual(keys, ["email_id"])
		self.assertIn("email_id", result["rows"])
