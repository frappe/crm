import json

import frappe
from frappe.tests import IntegrationTestCase

from crm.api.sidebar import get_sidebar, get_sidebar_layer, save_sidebar_layer
from crm.fcrm.doctype.crm_sidebar.crm_sidebar import get_permission_query_conditions, has_permission
from crm.fcrm.doctype.crm_sidebar.layers import as_item, resolve
from crm.fcrm.doctype.crm_sidebar.reduction import reduce_layer
from crm.patches.v1_0 import add_customize_sidebar_menu_item

AGENT = "sidebar.agent@example.com"
OTHER_AGENT = "sidebar.other@example.com"
MANAGER = "sidebar.manager@example.com"
TODAY = [
	"home",
	"dashboard",
	"leads",
	"deals",
	"contacts",
	"organizations",
	"notes",
	"tasks",
	"calendar",
	"call_logs",
	"public_views",
	"pinned_views",
]


def make_user(email, *roles):
	if not frappe.db.exists("User", email):
		frappe.get_doc(
			{"doctype": "User", "email": email, "first_name": email.split("@")[0], "send_welcome_email": 0}
		).insert(ignore_permissions=True)
	frappe.get_doc("User", email).add_roles(*roles)
	return email


def keys(items):
	return [item["key"] for item in items]


def by_key(items, key):
	return next(item for item in items if item["key"] == key)


def edit(scope):
	"""The layer as the dialog opens it, plus a helper to save a changed copy."""
	layer = get_sidebar_layer(scope)
	return layer, layer["items"]


def move(items, key, before):
	item = by_key(items, key)
	items.remove(item)
	items.insert(keys(items).index(before), item)


class TestSidebarLayers(IntegrationTestCase):
	def setUp(self):
		make_user(AGENT, "Sales User")
		make_user(OTHER_AGENT, "Sales User")
		make_user(MANAGER, "Sales User", "Sales Manager")
		frappe.db.delete("CRM Sidebar")
		frappe.db.delete("CRM Sidebar Item", {"parenttype": "CRM Sidebar"})
		self.addCleanup(frappe.set_user, "Administrator")

	def save(self, scope, layer, items):
		return save_sidebar_layer(scope, items, layer["modified"], layer["site_modified"])

	def test_an_untouched_site_draws_todays_sidebar(self):
		frappe.set_user(AGENT)
		self.assertEqual(keys(get_sidebar()), TODAY)
		self.assertFalse(frappe.db.count("CRM Sidebar"))

	def test_user_layer_wins_over_site_layer(self):
		frappe.set_user(MANAGER)
		layer, items = edit("site")
		by_key(items, "deals")["label"] = "Opportunities"
		by_key(items, "call_logs")["hidden"] = 1
		self.save("site", layer, items)

		frappe.set_user(AGENT)
		self.assertEqual(by_key(get_sidebar(), "deals")["label"], "Opportunities")
		self.assertNotIn("call_logs", keys(get_sidebar()))

		layer, items = edit("user")
		self.assertEqual(by_key(items, "call_logs")["hidden_by"], "site")
		by_key(items, "deals")["label"] = "My deals"
		by_key(items, "call_logs")["hidden"] = 0
		self.save("user", layer, items)

		sidebar = get_sidebar()
		self.assertEqual(by_key(sidebar, "deals")["label"], "My deals")
		self.assertIn("call_logs", keys(sidebar))
		frappe.set_user(OTHER_AGENT)
		self.assertEqual(by_key(get_sidebar(), "deals")["label"], "Opportunities")

	def test_a_layer_stores_only_its_changes(self):
		frappe.set_user(AGENT)
		layer, items = edit("user")
		move(items, "contacts", "leads")
		by_key(items, "notes")["label"] = "Notebook"
		self.save("user", layer, items)

		rows = frappe.get_all(
			"CRM Sidebar Item", filters={"parent": AGENT}, fields=["key", "overrides", "anchors"]
		)
		self.assertEqual(
			{row.key: (row.overrides, row.anchors) for row in rows},
			{"contacts": (None, json.dumps([{"after": "dashboard"}])), "notes": ('["label"]', None)},
		)
		self.assertEqual(keys(get_sidebar())[1:5], ["dashboard", "contacts", "leads", "deals"])

	def test_later_site_changes_reach_a_user_who_changed_other_rows(self):
		frappe.set_user(AGENT)
		layer, items = edit("user")
		by_key(items, "deals")["label"] = "My deals"
		self.save("user", layer, items)

		frappe.set_user(MANAGER)
		layer, items = edit("site")
		by_key(items, "deals")["hidden"] = 1
		by_key(items, "notes")["label"] = "Notebook"
		self.save("site", layer, items)

		frappe.set_user(AGENT)
		sidebar = get_sidebar()
		self.assertNotIn("deals", keys(sidebar))
		self.assertEqual(by_key(sidebar, "notes")["label"], "Notebook")

	def test_saving_the_layer_below_removes_the_layer(self):
		frappe.set_user(AGENT)
		layer, items = edit("user")
		by_key(items, "deals")["hidden"] = 1
		self.save("user", layer, items)
		self.assertTrue(frappe.db.exists("CRM Sidebar", {"user": AGENT}))

		layer = get_sidebar_layer("user")
		self.save("user", layer, layer["below"])
		self.assertFalse(frappe.db.exists("CRM Sidebar", {"user": AGENT}))
		self.assertEqual(keys(get_sidebar()), TODAY)

	def test_a_user_save_fails_when_the_site_layer_changed(self):
		frappe.set_user(AGENT)
		layer, items = edit("user")
		by_key(items, "leads")["label"] = "Prospects"

		frappe.set_user(MANAGER)
		site, site_items = edit("site")
		by_key(site_items, "call_logs")["hidden"] = 1
		self.save("site", site, site_items)

		frappe.set_user(AGENT)
		with self.assertRaises(frappe.TimestampMismatchError):
			save_sidebar_layer("user", items, layer["modified"], layer["site_modified"])

	def test_a_desk_write_is_validated_too(self):
		frappe.set_user(MANAGER)
		doc = frappe.get_doc(
			{
				"doctype": "CRM Sidebar",
				"items": [{"key": "site:lead01", "added": 1, "link_type": "DocType", "link_to": "CRM Lead"}],
			}
		)
		with self.assertRaises(frappe.ValidationError):
			doc.insert()
		doc.items[0].update({"key": "user:prd001", "link_to": "CRM Product"})
		with self.assertRaises(frappe.ValidationError):
			doc.insert()

	def test_a_stale_save_fails(self):
		frappe.set_user(AGENT)
		layer, items = edit("user")
		by_key(items, "deals")["hidden"] = 1
		self.save("user", layer, items)
		with self.assertRaises(frappe.TimestampMismatchError):
			self.save("user", layer, items)

	def test_a_user_adds_a_section_with_a_doctype_in_it(self):
		frappe.set_user(AGENT)
		layer, items = edit("user")
		section = {
			"key": "user:sec001",
			"type": "Section",
			"label": "Setup",
			"collapsible": 1,
			"keep_closed": 1,
		}
		product = {
			"key": "user:prd001",
			"link_type": "DocType",
			"link_to": "CRM Product",
			"parent_key": "user:sec001",
		}
		at = keys(items).index("public_views")
		items[at:at] = [section, product, {**by_key(items, "tasks"), "parent_key": "user:sec001"}]
		items.remove(next(item for item in items if item["key"] == "tasks" and not item.get("parent_key")))
		self.save("user", layer, items)

		sidebar = get_sidebar()
		self.assertEqual(
			keys(sidebar)[-5:], ["user:sec001", "user:prd001", "tasks", "public_views", "pinned_views"]
		)
		self.assertEqual(by_key(sidebar, "user:prd001")["label"], "CRM Product")
		self.assertEqual(by_key(sidebar, "tasks")["parent_key"], "user:sec001")

	def test_items_cannot_go_into_a_standard_section(self):
		frappe.set_user(AGENT)
		layer, items = edit("user")
		by_key(items, "tasks")["parent_key"] = "public_views"
		with self.assertRaises(frappe.ValidationError):
			self.save("user", layer, items)

	def test_refused_doctypes(self):
		frappe.set_user(AGENT)
		layer, items = edit("user")
		for doctype in ("CRM Lead", "CRM Sidebar Item", "FCRM Settings", "Error Log", "No Such Doctype"):
			row = {"key": "user:new001", "link_type": "DocType", "link_to": doctype}
			with self.assertRaises(frappe.ValidationError, msg=doctype):
				self.save("user", layer, [*items, row])

		layer, items = edit("user")
		first = {"key": "user:new001", "link_type": "DocType", "link_to": "CRM Product"}
		second = {**first, "key": "user:new002"}
		with self.assertRaises(frappe.ValidationError):
			self.save("user", layer, [*items, first, second])

	def test_only_managers_write_the_site_layer(self):
		frappe.set_user(AGENT)
		with self.assertRaises(frappe.PermissionError):
			get_sidebar_layer("site")
		layer = get_sidebar_layer("user")
		self.assertFalse(layer["can_edit_site"])
		with self.assertRaises(frappe.PermissionError):
			save_sidebar_layer("site", layer["items"], None)

	def test_each_user_reaches_only_their_own_layer(self):
		frappe.set_user(AGENT)
		layer, items = edit("user")
		by_key(items, "deals")["hidden"] = 1
		self.save("user", layer, items)
		frappe.set_user(MANAGER)
		layer, items = edit("site")
		by_key(items, "notes")["hidden"] = 1
		self.save("site", layer, items)

		mine, site = frappe.get_doc("CRM Sidebar", AGENT), frappe.get_doc("CRM Sidebar", "Site")
		self.assertTrue(has_permission(mine, "read", AGENT))
		self.assertFalse(has_permission(mine, "read", OTHER_AGENT))
		self.assertFalse(has_permission(mine, "write", MANAGER))
		self.assertTrue(has_permission(site, "read", AGENT))
		self.assertFalse(has_permission(site, "write", AGENT))
		self.assertTrue(has_permission(site, "write", MANAGER))

		frappe.set_user(OTHER_AGENT)
		self.assertEqual(frappe.get_list("CRM Sidebar", pluck="name"), ["Site"])
		self.assertIn(frappe.db.escape(OTHER_AGENT), get_permission_query_conditions())
		self.assertEqual(get_permission_query_conditions("Administrator"), "")

	def test_deleting_a_user_deletes_their_layer(self):
		user = make_user("sidebar.leaver@example.com", "Sales User")
		frappe.set_user(user)
		layer, items = edit("user")
		by_key(items, "deals")["hidden"] = 1
		self.save("user", layer, items)
		frappe.set_user("Administrator")
		frappe.delete_doc("User", user)
		self.assertFalse(frappe.db.exists("CRM Sidebar", {"user": user}))


BASE = [{"key": key, "label": key} for key in ("a", "b", "c", "d")]


class TestAnchors(IntegrationTestCase):
	def test_a_move_survives_a_new_standard_item(self):
		desired = [{"key": key} for key in ("c", "a", "b", "d")]
		rows = reduce_layer(resolve(BASE, []), desired, "site")
		self.assertEqual(rows, [{"key": "c", "type": "Link", "anchors": json.dumps([{"before": "a"}])}])

		shipped = [*BASE[:2], {"key": "new", "label": "new"}, *BASE[2:]]
		self.assertEqual(keys(resolve(shipped, [rows])), ["c", "a", "b", "new", "d"])

	def test_an_anchor_to_a_removed_item_keeps_the_hook_order(self):
		rows = [{"key": "d", "anchors": json.dumps([{"after": "gone"}])}]
		self.assertEqual(keys(resolve(BASE, [rows])), ["a", "b", "c", "d"])

	def test_a_section_anchored_after_a_lower_section_stays_above_the_views(self):
		standard = [
			*BASE,
			{"key": "public_views", "type": "Section"},
			{"key": "pinned_views", "type": "Section"},
		]
		sales = {"key": "site:sales1", "type": "Section", "label": "Sales"}
		site_rows = reduce_layer(resolve(standard, []), [*BASE, sales, *standard[4:]], "site")
		below = resolve(standard, [site_rows])

		added = [
			{"key": "user:docta1", "link_type": "DocType", "link_to": "A", "parent_key": "site:sales1"},
			{"key": "user:doctb1", "link_type": "DocType", "link_to": "B", "parent_key": "site:sales1"},
			{"key": "user:mine01", "type": "Section", "label": "Mine"},
		]
		desired = [*below[:5], *added, *below[5:]]
		user_rows = reduce_layer(below, desired, "user")
		self.assertEqual(
			keys(resolve(standard, [site_rows, user_rows])), keys([as_item(item) for item in desired])
		)

	def test_the_reduction_round_trips(self):
		desired = [{"key": key} for key in ("d", "b", "a", "c")]
		rows = reduce_layer(resolve(BASE, []), desired, "site")
		self.assertEqual(keys(resolve(BASE, [rows])), ["d", "b", "a", "c"])


class TestCustomizeSidebarPatch(IntegrationTestCase):
	def test_the_menu_item_lands_after_settings(self):
		# A site from before the item, whose admin moved Settings to the end of the menu.
		table = {"parenttype": "FCRM Settings", "parentfield": "dropdown_items"}
		frappe.db.delete("CRM Dropdown Item", {**table, "name1": "customize_sidebar"})
		last = max(frappe.get_all("CRM Dropdown Item", filters=table, pluck="idx"))
		frappe.db.set_value("CRM Dropdown Item", {**table, "name1": "settings"}, "idx", last + 1)

		add_customize_sidebar_menu_item.execute()
		names = [row.name1 for row in frappe.get_single("FCRM Settings").dropdown_items]
		self.assertEqual(names[-2:], ["settings", "customize_sidebar"])

		add_customize_sidebar_menu_item.execute()
		names = [row.name1 for row in frappe.get_single("FCRM Settings").dropdown_items]
		self.assertEqual(names.count("customize_sidebar"), 1)
