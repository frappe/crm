import inspect

import frappe
from frappe.model.document import get_controller
from frappe.model.meta import Meta
from frappe.tests import IntegrationTestCase

from crm.api import doc, list_view
from crm.api.list_defaults import MetaListDefaults
from crm.api.views import get_views
from crm.fcrm.doctype.crm_deal.test_crm_deal import create_test_deal
from crm.tests.test_record_api import AgentApiRules

REPLACED = {
	"get_data": "get_list_view",
	"sort_options": "get_sort_fields",
	"get_filterable_fields": "get_filter_fields",
	"get_group_by_fields": "get_group_by_fields",
	"get_quick_filters": "get_quick_filters",
	"update_quick_filters": "set_quick_filters",
}
BUILT_IN = ("CRM Lead", "CRM Deal", "CRM Organization", "Contact", "CRM Task", "FCRM Note", "CRM Call Log")
KANBAN = ("CRM Lead", "CRM Deal", "CRM Task")
READS_WITH_POST = frozenset({"get_list_view", "get_kanban_view"})
READS = frozenset(
	{
		"get_sort_fields",
		"get_filter_fields",
		"get_group_by_fields",
		"get_quick_filters",
		"get_column_fields",
		"get_views",
		"get_list_scripts",
	}
)


class TestListViewApiRules(AgentApiRules, IntegrationTestCase):
	api_module = list_view
	methods = READS | READS_WITH_POST | {"set_quick_filters"}
	reads = READS
	reads_with_post = READS_WITH_POST

	def test_reads_do_not_write(self):
		frappe.set_user("Administrator")
		writes = frappe.db.transaction_writes
		for name in sorted(READS | READS_WITH_POST):
			getattr(list_view, name)("CRM Lead")
		self.assertEqual(frappe.db.transaction_writes, writes)


class TestDeprecatedListMethods(IntegrationTestCase):
	"""The old crm.api.doc list paths stay whitelisted and point to their replacements."""

	def setUp(self):
		frappe.set_user("Administrator")

	def test_old_paths_name_their_replacement(self):
		for old, new in REPLACED.items():
			fn = getattr(doc, old)
			replacement = f"crm.api.list_view.{new}"
			self.assertIn(fn, frappe.whitelisted, old)
			self.assertEqual(fn.replaced_by, replacement)
			self.assertEqual(inspect.getdoc(fn), f"Deprecated: use {replacement}.")
			self.assertIn(frappe.get_attr(replacement), frappe.whitelisted)

	def test_old_update_quick_filters_still_accepts_json_text(self):
		frappe.db.delete("CRM Global Settings", {"dt": "CRM Deal", "type": "Quick Filters"})

		doc.update_quick_filters('["name", "status"]', "[]", "CRM Deal")

		filters = list_view.get_quick_filters("CRM Deal", cached=False)
		self.assertEqual([f["fieldname"] for f in filters], ["name", "status"])
		self.assertTrue(frappe.get_meta("CRM Deal", cached=False).get_field("status").in_standard_filter)

	def test_set_quick_filters_drops_the_old_standard_filters(self):
		frappe.db.delete("CRM Global Settings", {"dt": "CRM Deal", "type": "Quick Filters"})
		list_view.set_quick_filters("CRM Deal", ["status"])

		list_view.set_quick_filters("CRM Deal", ["deal_owner"])

		meta = frappe.get_meta("CRM Deal", cached=False)
		self.assertFalse(meta.get_field("status").in_standard_filter)
		self.assertTrue(meta.get_field("deal_owner").in_standard_filter)

	def test_set_quick_filters_rejects_unknown_fields(self):
		with self.assertRaises(frappe.ValidationError):
			list_view.set_quick_filters("CRM Deal", ["no_such_field"])

	def test_set_quick_filters_needs_a_manager(self):
		frappe.set_user("crm.user1@example.com")
		with self.assertRaises(frappe.PermissionError):
			list_view.set_quick_filters("CRM Deal", ["status"])


class TestBuiltInDoctypes(IntegrationTestCase):
	"""Built-in doctypes get from the new methods what get_data returns, and get_data keeps its rules."""

	def setUp(self):
		frappe.set_user("Administrator")
		frappe.db.delete("CRM View Settings", {"is_standard": 1, "user": "Administrator"})
		create_test_deal(organization="List View API Org")

	def test_list_view_matches_get_data(self):
		for doctype in BUILT_IN:
			old = get_data(doctype, "list")
			new = list_view.get_list_view(doctype, filters={}, order_by="modified desc")

			default_keys = [c["key"] for c in get_controller(doctype).default_list_data()["columns"]]
			self.assertEqual([c["key"] for c in old["columns"]], default_keys, doctype)
			self.assertEqual(new["columns"], [lean(c) for c in old["columns"]], doctype)
			self.assertEqual(new["records"], old["data"], doctype)
			self.assertEqual(new["total"], old["total_count"], doctype)

	def test_group_by_view_matches_get_data(self):
		for doctype in BUILT_IN:
			old = get_data(doctype, "group_by", group_by_field="owner")
			new = list_view.get_list_view(
				doctype, filters={}, order_by="modified desc", view_type="group_by", group_by_field="owner"
			)
			self.assertEqual(new["records"], old["data"], doctype)
			self.assertEqual(new["view"]["group_by_field"], "owner", doctype)

	def test_kanban_view_matches_get_data(self):
		for doctype in KANBAN:
			old = get_data(doctype, "kanban", column_field="status")
			new = list_view.get_kanban_view(doctype, filters={}, order_by="modified desc")

			self.assertEqual(new["view"]["column_field"], "status", doctype)
			self.assertEqual(new["view"]["title_field"], old["title_field"], doctype)
			self.assertEqual(new["view"]["card_fields"], old["kanban_fields"], doctype)
			self.assertEqual([c["name"] for c in new["columns"]], [c["column"]["name"] for c in old["data"]])
			self.assertEqual([c["records"] for c in new["columns"]], [c["data"] for c in old["data"]])

	def test_standard_view_row_comes_before_the_controller(self):
		frappe.get_doc(
			doctype="CRM View Settings",
			label="My deals",
			dt="CRM Deal",
			user="Administrator",
			type="list",
			is_standard=1,
			columns='[{"key": "organization", "label": "Organization", "type": "Link", "width": "10rem"}]',
			rows='["name", "organization"]',
		).insert()

		old = get_data("CRM Deal", "list")
		new = list_view.get_list_view("CRM Deal", filters={}, order_by="modified desc")

		self.assertFalse(old["is_default"])
		self.assertEqual([c["key"] for c in old["columns"]], ["organization"])
		self.assertEqual(new["columns"], [lean(c) for c in old["columns"]])

	def test_custom_view_with_default_columns_is_default(self):
		view = frappe.get_doc(
			doctype="CRM View Settings", label="Defaults", dt="CRM Deal", type="list", load_default_columns=1
		).insert()
		columns = frappe.as_json([{"key": "status", "label": "Status", "type": "Link", "width": "8rem"}])

		old = get_data("CRM Deal", "list", custom_view_name=view.name, columns=columns, rows='["name"]')

		self.assertEqual(old["is_default"], 1)

	def test_kanban_column_order_and_deleted_columns(self):
		statuses = frappe.get_all("CRM Deal Status", pluck="name", order_by="position asc")[:2]
		deals = [create_test_deal(organization=f"Kanban Order Org {i}", status=statuses[0]) for i in range(2)]
		kanban_columns = [
			{"name": statuses[0], "order": [deals[0].name, deals[1].name]},
			{"name": statuses[1], "delete": True},
		]

		old = get_data(
			"CRM Deal", "kanban", column_field="status", kanban_columns=frappe.as_json(kanban_columns)
		)

		first, deleted = old["data"]
		self.assertEqual([d["name"] for d in first["data"][:2]], [deals[0].name, deals[1].name])
		self.assertEqual(deleted["data"], [])
		self.assertNotIn("count", deleted["column"])

	def test_group_by_link_options_follow_the_sort(self):
		orgs = ["Group Sort Org A", "Group Sort Org B"]
		for org in orgs:
			create_test_deal(organization=org)

		old = doc.get_data(
			doctype="CRM Deal",
			filters={"organization": ["in", orgs]},
			order_by="organization desc",
			view={"view_type": "group_by", "group_by_field": "organization"},
		)

		self.assertEqual(old["group_by_field"]["options"], list(reversed(orgs)))

	def test_list_view_adds_extra_fields_to_the_defaults(self):
		result = list_view.get_list_view("CRM Deal", fields=["probability"])

		default_keys = [c["key"] for c in get_controller("CRM Deal").default_list_data()["columns"]]
		self.assertEqual([c["key"] for c in result["columns"]], default_keys)
		self.assertIn("probability", result["records"][0])
		self.assertIn("organization", result["records"][0])

	def test_get_data_keeps_the_parts_moved_out(self):
		old = get_data("CRM Deal", "list")
		scripts = list_view.get_list_scripts("CRM Deal")

		self.assertEqual(old["fields"], list_view.get_column_fields("CRM Deal"))
		self.assertEqual(old["views"], get_views("CRM Deal"))
		self.assertEqual(old["form_script"], scripts["form_script"])
		self.assertEqual(old["list_script"], scripts["list_script"])
		self.assertEqual(set(old), GET_DATA_KEYS)


class TestListViewDefaults(IntegrationTestCase):
	"""A doctype with no list hooks gets its list view from meta."""

	def setUp(self):
		frappe.set_user("Administrator")
		frappe.db.delete("CRM View Settings", {"dt": ("in", ("ToDo", "Note"))})
		frappe.get_doc({"doctype": "ToDo", "description": "List view defaults row"}).insert()

	def test_no_hooks_gets_title_and_in_list_view_columns(self):
		meta = frappe.get_meta("ToDo")
		in_list_view = [
			f.fieldname for f in meta.fields if f.in_list_view and f.fieldname != meta.title_field
		]

		result = list_view.get_list_view("ToDo")

		keys = [c["key"] for c in result["columns"]]
		self.assertEqual(keys, [meta.title_field, *in_list_view, "modified"][:7])
		self.assertEqual(result["view"]["order_by"], f"{meta.sort_field} {meta.sort_order}".lower())
		self.assertTrue(result["records"])

	def test_group_by_defaults_to_the_status_select(self):
		result = list_view.get_list_view("ToDo", view_type="group_by")
		self.assertEqual(result["view"]["group_by_field"], "status")

	def test_kanban_cards_have_a_name(self):
		result = list_view.get_kanban_view("ToDo")
		records = [r for column in result["columns"] for r in column["records"]]

		self.assertTrue(records)
		self.assertTrue(all(r["name"] for r in records))
		self.assertNotIn("", [column["name"] for column in result["columns"]])

	def test_kanban_column_field_must_be_a_select_or_link(self):
		with self.assertRaises(frappe.ValidationError):
			list_view.get_kanban_view("ToDo", column_field="description")
		with self.assertRaises(frappe.ValidationError):
			list_view.get_kanban_view("ToDo", column_field="no_such_field")

	def test_kanban_without_a_select_field_has_no_columns(self):
		result = list_view.get_kanban_view("Note")
		self.assertIsNone(result["view"]["column_field"])
		self.assertEqual(result["columns"], [])
		self.assertEqual(result["view"]["title_field"], "title")

	def test_saved_view_fills_the_arguments_left_out(self):
		view = frappe.get_doc(
			doctype="CRM View Settings",
			label="Open todos",
			dt="ToDo",
			user="Administrator",
			type="list",
			filters='{"status": "Open"}',
			order_by="creation asc",
			columns='[{"key": "status", "label": "Status", "type": "Select", "width": "8rem"}]',
			rows='["name"]',
		).insert()

		result = list_view.get_list_view("ToDo", view_name=view.name)

		self.assertEqual(result["view"]["filters"], {"status": "Open"})
		self.assertEqual(result["view"]["order_by"], "creation asc")
		self.assertEqual([c["key"] for c in result["columns"]], ["status"])
		self.assertTrue(all(r["status"] == "Open" for r in result["records"]))

		frappe.set_user("crm.user1@example.com")
		with self.assertRaises(frappe.PermissionError):
			list_view.get_list_view("ToDo", view_name=view.name)


class TestMetaListDefaults(IntegrationTestCase):
	"""The column and Group by rules, on doctypes built in memory."""

	def test_title_field_then_list_fields_then_modified(self):
		defaults = meta_defaults([field("title"), field("city", in_list_view=1)], title_field="title")
		self.assertEqual(keys(defaults), ["title", "city", "modified"])

	def test_name_first_without_a_title_field(self):
		defaults = meta_defaults([field("city", in_list_view=1)])
		self.assertEqual(keys(defaults), ["name", "city", "modified"])

	def test_name_and_modified_when_meta_gives_nothing(self):
		self.assertEqual(keys(meta_defaults([field("notes", "Small Text")])), ["name", "modified"])

	def test_few_list_fields_are_topped_up_to_four(self):
		fields = [
			field("city", in_list_view=1),
			field("notes", "Small Text", reqd=1),
			field("region", in_standard_filter=1),
			field("owner_email", reqd=1),
			field("zip", in_standard_filter=1),
			field("country", reqd=1),
		]
		self.assertEqual(
			keys(meta_defaults(fields)), ["name", "city", "region", "owner_email", "zip", "modified"]
		)

	def test_at_most_seven_columns(self):
		defaults = meta_defaults([field(f"field_{i}", in_list_view=1) for i in range(10)], is_submittable=1)
		self.assertEqual(len(defaults.columns), 7)
		self.assertEqual(keys(defaults)[-2:], ["docstatus", "modified"])

	def test_submittable_shows_its_own_status_field(self):
		defaults = meta_defaults([field("status", "Select", options="Draft\nPaid")], is_submittable=1)
		self.assertEqual(keys(defaults), ["name", "status", "modified"])

	def test_group_by_field_prefers_status_then_list_view_select(self):
		region = field("region", "Select", options="N\nS")
		kind = field("kind", "Select", options="A\nB", in_list_view=1)
		status = field("status", "Select", options="Open\nClosed")
		party = field("party", "Link", options="User", in_list_view=1)

		self.assertEqual(meta_defaults([region, kind, status, party]).select_field, "status")
		self.assertEqual(meta_defaults([region, kind, party]).select_field, "kind")
		self.assertEqual(meta_defaults([region, party]).select_field, "region")
		self.assertIsNone(meta_defaults([party]).select_field)

	def test_naming_series_is_never_a_default(self):
		series = field("naming_series", "Select", options="DEAL-.#####", reqd=1, in_standard_filter=1)
		defaults = meta_defaults([series, field("city", in_list_view=1)])
		self.assertIsNone(defaults.select_field)
		self.assertEqual(keys(defaults), ["name", "city", "modified"])


GET_DATA_KEYS = {
	"data",
	"columns",
	"rows",
	"fields",
	"column_field",
	"title_field",
	"kanban_columns",
	"kanban_fields",
	"group_by_field",
	"page_length",
	"page_length_count",
	"is_default",
	"views",
	"total_count",
	"row_count",
	"form_script",
	"list_script",
	"view_type",
}


def get_data(doctype, view_type, **kwargs):
	view = {
		"view_type": view_type,
		"group_by_field": kwargs.pop("group_by_field", None),
		"custom_view_name": kwargs.pop("custom_view_name", None),
	}
	return doc.get_data(doctype=doctype, filters={}, order_by="modified desc", view=view, **kwargs)


def lean(column):
	return {key: column.get(key) for key in ("key", "label", "type", "width")}


def field(fieldname, fieldtype="Data", **properties):
	return {"fieldname": fieldname, "label": fieldname.title(), "fieldtype": fieldtype, **properties}


def meta_defaults(fields, **properties):
	doctype = frappe.get_doc(
		{"doctype": "DocType", "name": "List Defaults Test", "module": "FCRM", "fields": fields, **properties}
	)
	return MetaListDefaults(Meta(doctype))


def keys(defaults):
	return [column["key"] for column in defaults.columns]
