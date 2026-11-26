import frappe
from frappe.model.document import get_controller
from frappe.tests import IntegrationTestCase

from crm.api.doc import get_data

# ToDo's controller has none of the optional list hooks that CRM doctypes define
DOCTYPE = "ToDo"
LIST_HOOKS = ("default_list_data", "default_kanban_settings", "parse_list_data")


def todo_view(view_type, **kwargs):
	return get_data(
		doctype=DOCTYPE,
		filters={},
		order_by="modified desc",
		page_length=5,
		view={"view_type": view_type},
		**kwargs,
	)


class TestGenericDoctypeList(IntegrationTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		frappe.db.delete("CRM View Settings", {"dt": DOCTYPE})
		frappe.get_doc({"doctype": DOCTYPE, "description": "Generic list row"}).insert()

	def tearDown(self):
		frappe.db.rollback()

	def test_controller_has_no_list_hooks(self):
		controller = get_controller(DOCTYPE)
		for hook in LIST_HOOKS:
			self.assertFalse(hasattr(controller, hook), hook)

	def test_list_falls_back_to_name_and_modified(self):
		result = todo_view("list")

		self.assertTrue(result["is_default"])
		self.assertEqual([column["key"] for column in result["columns"]], ["name", "modified"])
		self.assertIn("modified", result["rows"])
		self.assertTrue(result["data"])

	def test_group_by_falls_back_to_name_and_modified(self):
		result = todo_view("group_by")

		self.assertEqual([column["key"] for column in result["columns"]], ["name", "modified"])

	def test_kanban_falls_back_to_name(self):
		result = todo_view("kanban", column_field="status")

		self.assertEqual(result["title_field"], "name")
		self.assertEqual(result["kanban_fields"], ["name"])
		self.assertEqual(
			[column["column"]["name"] for column in result["data"]], ["Open", "Closed", "Cancelled"]
		)
