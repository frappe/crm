import frappe
from frappe.model.document import get_controller
from frappe.tests import IntegrationTestCase

from crm.api.doc import get_data
from crm.api.list_defaults import MetaListDefaults

# ToDo's controller has none of the optional list hooks that CRM doctypes define
DOCTYPE = "ToDo"
LIST_HOOKS = ("default_list_data", "default_kanban_settings", "parse_list_data")


def todo_view(view_type, group_by_field=None, **kwargs):
	return get_data(
		doctype=DOCTYPE,
		filters={},
		order_by="modified desc",
		page_length=5,
		view={"view_type": view_type, "group_by_field": group_by_field},
		**kwargs,
	)


def meta_column_keys():
	return [column["key"] for column in MetaListDefaults(frappe.get_meta(DOCTYPE)).columns]


def status_options():
	return frappe.get_meta(DOCTYPE).get_field("status").options.split("\n")


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

	def test_list_gets_columns_from_meta(self):
		result = todo_view("list")

		self.assertTrue(result["is_default"])
		self.assertEqual([column["key"] for column in result["columns"]], meta_column_keys())
		self.assertIn("modified", result["rows"])
		self.assertTrue(result["data"])

	def test_group_by_gets_columns_from_meta(self):
		result = todo_view("group_by", group_by_field="status")

		self.assertEqual([column["key"] for column in result["columns"]], meta_column_keys())
		self.assertEqual(result["group_by_field"]["options"], status_options())

	def test_kanban_gets_title_and_card_fields_from_meta(self):
		defaults = MetaListDefaults(frappe.get_meta(DOCTYPE))
		result = todo_view("kanban", column_field="status")

		self.assertEqual(result["title_field"], defaults.title_field)
		self.assertEqual(result["kanban_fields"], defaults.get_card_fields("status"))
		self.assertEqual([column["column"]["name"] for column in result["data"]], status_options())
