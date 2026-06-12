# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

<<<<<<< HEAD
# import frappe
from frappe.tests.utils import FrappeTestCase
=======
import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
from frappe.tests import IntegrationTestCase
>>>>>>> b2d9622f (feat: create products as Items in ERPNext)

from crm.fcrm.doctype.crm_product.crm_product import sync_item_to_crm_product


<<<<<<< HEAD
<<<<<<< HEAD
class TestCRMProduct(FrappeTestCase):
	"""
	Unit tests for CRMProduct.
	Use this class for testing individual functions and methods.
	"""

	pass
=======
=======
def _ensure_erpnext_item_code_field():
	if frappe.db.has_column("CRM Product", "erpnext_item_code"):
		return
	create_custom_fields(
		{
			"CRM Product": [
				{
					"fieldname": "erpnext_item_code",
					"fieldtype": "Data",
					"label": "Item Code in ERPNext",
					"read_only": 1,
					"insert_after": "product_code",
				}
			]
		},
		ignore_validate=True,
	)


>>>>>>> 5c755216 (fix: failing tests)
def _make_item_doc(item_code, **fields):
	"""Build a item_doc that works like a Frappe doc for our handler."""
	data = {
		"item_code": item_code,
		"item_name": item_code,
		"standard_rate": 0,
		"image": None,
		"disabled": 0,
		"description": None,
		"flags": frappe._dict(),
	}
	data.update(fields)
	return frappe._dict(data)


class IntegrationTestCRMProduct(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		_ensure_erpnext_item_code_field()

	def setUp(self):
		frappe.db.set_single_value("ERPNext CRM Settings", "enabled", 1)

	def tearDown(self):
		frappe.db.rollback()

	# before_insert guard

	def test_before_insert_blocks_when_enabled(self):
		product = frappe.new_doc("CRM Product")
		product.product_code = "TEST-PROD-BLOCK"
		with self.assertRaises(frappe.ValidationError):
			product.insert()

	def test_before_insert_allows_with_ignore_flag(self):
		product = frappe.new_doc("CRM Product")
		product.product_code = "TEST-PROD-FLAG"
		product.flags.ignore_erpnext_sync = True
		product.insert(ignore_permissions=True)
		self.assertTrue(frappe.db.exists("CRM Product", "TEST-PROD-FLAG"))

	def test_before_insert_allows_when_disabled(self):
		frappe.db.set_single_value("ERPNext CRM Settings", "enabled", 0)
		product = frappe.new_doc("CRM Product")
		product.product_code = "TEST-PROD-OFF"
		product.insert()
		self.assertTrue(frappe.db.exists("CRM Product", "TEST-PROD-OFF"))

	# sync_item_to_crm_product — three resolution paths

	def test_sync_updates_existing_linked_crm_product(self):
		self._make_product("LINKED-001", erpnext_item_code="ITEM-001", product_name="Old Name")
		sync_item_to_crm_product(_make_item_doc("ITEM-001", item_name="New Name", standard_rate=99))
		self.assertEqual(frappe.db.get_value("CRM Product", "LINKED-001", "product_name"), "New Name")
		self.assertEqual(frappe.db.get_value("CRM Product", "LINKED-001", "standard_rate"), 99)

	def test_sync_creates_new_crm_product_when_no_match(self):
		sync_item_to_crm_product(_make_item_doc("ITEM-003", item_name="Brand New", standard_rate=50))
		self.assertTrue(frappe.db.exists("CRM Product", "ITEM-003"))
		self.assertEqual(frappe.db.get_value("CRM Product", "ITEM-003", "erpnext_item_code"), "ITEM-003")
		self.assertEqual(frappe.db.get_value("CRM Product", "ITEM-003", "product_name"), "Brand New")

	def test_sync_no_op_when_integration_disabled(self):
		frappe.db.set_single_value("ERPNext CRM Settings", "enabled", 0)
		sync_item_to_crm_product(_make_item_doc("ITEM-OFF"))
		self.assertFalse(frappe.db.exists("CRM Product", "ITEM-OFF"))

	def test_sync_honors_ignore_crm_sync_flag(self):
		item = _make_item_doc("ITEM-FLAG")
		item.flags.ignore_crm_sync = True
		sync_item_to_crm_product(item)
		self.assertFalse(frappe.db.exists("CRM Product", "ITEM-FLAG"))

	# on_update push behavior

	def test_on_update_no_op_without_erpnext_item_code(self):
		"""CRM-only products (no link) should not push."""
		product = self._make_product("UNLINKED-001", product_name="Original")
		calls = self._patch_push()
		product.product_name = "Edited"
		product.save()
		self._unpatch_push()
		self.assertEqual(calls, [])

	def test_on_update_pushes_when_synced_field_changes(self):
		product = self._make_product("PUSH-001", erpnext_item_code="ITEM-PUSH", product_name="Old")
		calls = self._patch_push()
		product.product_name = "New"
		product.save()
		self._unpatch_push()
		self.assertEqual(calls, ["PUSH-001"])

	def test_push_clears_link_when_item_missing(self):
		"""Iif the linked Item no longer exists, erpnext_item_code should be cleared."""
		from crm.fcrm.doctype.crm_product.crm_product import push_product_to_erpnext_item

		product = self._make_product(
			"STALE-LINK-001", erpnext_item_code="ITEM-DOES-NOT-EXIST", product_name="Orphan"
		)
		push_product_to_erpnext_item(product)
		self.assertIsNone(frappe.db.get_value("CRM Product", "STALE-LINK-001", "erpnext_item_code"))

	def _make_product(self, product_code, **fields):
		product = frappe.new_doc("CRM Product")
		product.product_code = product_code
		for field, value in fields.items():
			product.set(field, value)
		product.flags.ignore_erpnext_sync = True
		product.insert(ignore_permissions=True)
		return frappe.get_doc("CRM Product", product.name)

	def _patch_push(self):
		import crm.fcrm.doctype.crm_product.crm_product as module

		self._push_original = module.push_product_to_erpnext_item
		calls = []
		module.push_product_to_erpnext_item = lambda doc: calls.append(doc.name)
		return calls

	def _unpatch_push(self):
		import crm.fcrm.doctype.crm_product.crm_product as module

		module.push_product_to_erpnext_item = self._push_original
>>>>>>> b2d9622f (feat: create products as Items in ERPNext)
