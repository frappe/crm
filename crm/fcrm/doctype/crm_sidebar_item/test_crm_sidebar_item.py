# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase

from crm.fcrm.doctype.crm_sidebar_item.crm_sidebar_item import get_sidebar_items
from crm.fcrm.doctype.fcrm_settings.fcrm_settings import after_migrate
from crm.install import after_app_uninstall

SALES_USER = "sidebar.sales.user@example.com"


class TestCRMSidebarItem(IntegrationTestCase):
	def tearDown(self) -> None:
		frappe.set_user("Administrator")
		frappe.db.rollback()
		frappe.clear_document_cache("FCRM Settings", "FCRM Settings")

	def add_doctype(self, settings, dt, **values):
		return settings.append("sidebar_items", {"type": "DocType", "dt": dt, **values})

	def keys(self, settings=None):
		settings = settings or frappe.get_single("FCRM Settings")
		return [item.name1 for item in settings.sidebar_items]

	def test_seeded_from_the_hook_in_order(self):
		standard_keys = [item["name1"] for item in frappe.get_hooks("standard_sidebar_items")]
		self.assertEqual(self.keys()[: len(standard_keys)], standard_keys)

	def test_built_in_item_cannot_be_deleted(self):
		settings = frappe.get_single("FCRM Settings")
		settings.sidebar_items = [item for item in settings.sidebar_items if item.name1 != "notes"]
		self.assertRaises(frappe.ValidationError, settings.save)

	def test_built_in_item_can_be_hidden_renamed_and_moved(self):
		settings = frappe.get_single("FCRM Settings")
		leads = next(item for item in settings.sidebar_items if item.name1 == "leads")
		leads.update({"hidden": 1, "label": "Prospects", "icon": "user-search"})
		settings.sidebar_items.remove(leads)
		settings.sidebar_items.append(leads)
		settings.save()

		settings.reload()
		self.assertEqual(self.keys(settings)[-1], "leads")
		self.assertEqual(settings.sidebar_items[-1].label, "Prospects")

	def test_hook_owns_a_built_in_route(self):
		settings = frappe.get_single("FCRM Settings")
		deals = next(item for item in settings.sidebar_items if item.name1 == "deals")
		deals.route = "Leads"
		settings.save()
		self.assertEqual(deals.route, "Deals")

	def test_doctype_item_gets_key_label_and_icon(self):
		settings = frappe.get_single("FCRM Settings")
		item = self.add_doctype(settings, "CRM Product")
		settings.save()
		self.assertTrue(item.name1.startswith("doctype-"))
		self.assertEqual(item.label, "CRM Product")
		self.assertEqual(item.icon, "file-text")

	def test_only_doctypes_with_a_list_can_be_added(self):
		for dt in ("FCRM Settings", "CRM Sidebar Item", "Error Log"):
			settings = frappe.get_single("FCRM Settings")
			self.add_doctype(settings, dt)
			self.assertRaises(frappe.ValidationError, settings.save)

	def test_doctype_cannot_be_added_twice(self):
		settings = frappe.get_single("FCRM Settings")
		self.add_doctype(settings, "CRM Product")
		self.add_doctype(settings, "CRM Product")
		self.assertRaises(frappe.ValidationError, settings.save)

	def test_custom_page_cannot_be_added(self):
		settings = frappe.get_single("FCRM Settings")
		settings.append("sidebar_items", {"type": "Page", "route": "Leads", "label": "Leads again"})
		self.assertRaises(frappe.ValidationError, settings.save)

	def test_sync_adds_a_new_built_in_page_at_the_end(self):
		settings = frappe.get_single("FCRM Settings")
		self.add_doctype(settings, "CRM Product")
		settings.save()
		frappe.db.delete("CRM Sidebar Item", {"parenttype": "FCRM Settings", "name1": "deals"})

		after_migrate()
		keys = self.keys()
		self.assertEqual(keys[-1], "deals")
		self.assertLess(keys.index("leads"), keys.index("contacts"))

	def test_sync_is_idempotent(self):
		after_migrate()
		keys = self.keys()
		after_migrate()
		self.assertEqual(self.keys(), keys)

	def test_uninstall_drops_a_deleted_doctype(self):
		"""An uninstalled app's DocType would fail every save on its dead link."""
		settings = frappe.get_single("FCRM Settings")
		item = self.add_doctype(settings, "CRM Product")
		settings.save()
		frappe.db.set_value("CRM Sidebar Item", item.name, "dt", "Gone DocType")

		after_app_uninstall("gone_app")
		self.assertNotIn(item.name1, self.keys())
		settings = frappe.get_single("FCRM Settings")
		settings.save()

	def test_crafted_built_in_item_is_refused(self):
		settings = frappe.get_single("FCRM Settings")
		settings.append(
			"sidebar_items", {"is_standard": 1, "name1": "made-up", "type": "Page", "route": "Leads"}
		)
		self.assertRaises(frappe.ValidationError, settings.save)

	def test_item_keys_are_unique(self):
		settings = frappe.get_single("FCRM Settings")
		self.add_doctype(settings, "CRM Product", name1="doctype-same")
		self.add_doctype(settings, "CRM Territory", name1="doctype-same")
		self.assertRaises(frappe.ValidationError, settings.save)

	def test_user_sees_visible_items_and_readable_doctypes(self):
		settings = frappe.get_single("FCRM Settings")
		next(item for item in settings.sidebar_items if item.name1 == "notes").hidden = 1
		readable = self.add_doctype(settings, "CRM Product")
		unreadable = self.add_doctype(settings, "Deleted Document")
		settings.save()

		frappe.set_user(make_sales_user())
		keys = [item["name1"] for item in get_sidebar_items()]
		self.assertIn("leads", keys)
		self.assertNotIn("notes", keys)
		self.assertIn(readable.name1, keys)
		self.assertNotIn(unreadable.name1, keys)


def make_sales_user() -> str:
	if not frappe.db.exists("User", SALES_USER):
		user = frappe.get_doc({"doctype": "User", "email": SALES_USER, "first_name": "Sidebar"})
		user.append("roles", {"role": "Sales User"})
		user.insert(ignore_permissions=True)
	return SALES_USER
