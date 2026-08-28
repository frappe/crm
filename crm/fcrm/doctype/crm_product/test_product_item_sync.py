import frappe
from frappe.tests.utils import FrappeTestCase

ITEM_GROUP = "All Item Groups"


def enable_product_sync():
	"""CI installs ERPNext but leaves the integration off; enable it and create the link fields.

	Mirrors what configuring the integration does, so the sync hooks and the
	``erpnext_item_code`` / ``crm_product_code`` custom fields are in place.
	"""
	settings = frappe.get_single("ERPNext CRM Settings")
	settings.enabled = 1
	settings.is_erpnext_in_different_site = 0
	settings.sync_products = 1
	settings.save(ignore_permissions=True)

	from crm.patches.v1_0.create_custom_fields_for_product_item_sync import execute

	execute()


def set_bidirectional_product_sync(value):
	frappe.db.set_single_value("ERPNext CRM Settings", "sync_products", value)
	frappe.clear_document_cache("ERPNext CRM Settings", "ERPNext CRM Settings")


class TestReverseLinkField(FrappeTestCase):
	def test_item_has_crm_product_code_field(self):
		if not frappe.db.exists("DocType", "Item"):
			self.skipTest("ERPNext not installed")
		enable_product_sync()
		self.assertTrue(frappe.db.has_column("Item", "crm_product_code"))


class TestEchoLoopBreaker(FrappeTestCase):
	def test_payload_identical_to_target_is_noop(self):
		from crm.fcrm.doctype.crm_product.sync_utils import payload_differs

		self.assertFalse(
			payload_differs(
				{"item_name": "Widget", "standard_rate": 10, "disabled": 0},
				{"item_name": "Widget", "standard_rate": 10, "disabled": 0},
			)
		)

	def test_payload_differs_when_any_field_changed(self):
		from crm.fcrm.doctype.crm_product.sync_utils import payload_differs

		self.assertTrue(
			payload_differs(
				{"item_name": "Widget", "standard_rate": 12},
				{"item_name": "Widget", "standard_rate": 10},
			)
		)

	def test_none_and_empty_string_treated_as_equal(self):
		from crm.fcrm.doctype.crm_product.sync_utils import payload_differs

		self.assertFalse(payload_differs({"description": ""}, {"description": None}))


class TestReconciliationRules(FrappeTestCase):
	def test_already_linked_pair_is_skipped(self):
		from crm.fcrm.doctype.crm_product.reconciliation import classify_pair

		item = {"item_code": "A", "crm_product_code": "A"}
		product = {"name": "A", "product_code": "A", "erpnext_item_code": "A"}
		self.assertEqual(classify_pair(item, product).rule, "already_linked")

	def test_exact_code_match_resolves_erpnext_wins_for_catalogue(self):
		from crm.fcrm.doctype.crm_product.reconciliation import classify_pair

		item = {"item_code": "B", "item_name": "From ERP", "standard_rate": 100}
		product = {
			"name": "B",
			"product_code": "B",
			"product_name": "From CRM",
			"standard_rate": 80,
		}
		result = classify_pair(item, product)
		self.assertEqual(result.rule, "exact_code")
		self.assertEqual(result.crm_updates["standard_rate"], 100)
		self.assertNotIn("product_name", result.crm_updates)

	def test_crm_name_filled_in_when_empty(self):
		from crm.fcrm.doctype.crm_product.reconciliation import classify_pair

		item = {"item_code": "C", "item_name": "Filled"}
		product = {"name": "C", "product_code": "C", "product_name": None}
		result = classify_pair(item, product)
		self.assertEqual(result.crm_updates["product_name"], "Filled")

	def test_orphan_detection(self):
		from crm.fcrm.doctype.crm_product.reconciliation import detect_orphan

		self.assertTrue(detect_orphan({"erpnext_item_code": "GONE"}, {"OTHER"}))
		self.assertFalse(detect_orphan({"erpnext_item_code": "HERE"}, {"HERE"}))
		self.assertFalse(detect_orphan({"erpnext_item_code": None}, set()))


class TestItemHooks(FrappeTestCase):
	def setUp(self):
		if not frappe.db.exists("DocType", "Item"):
			self.skipTest("ERPNext not installed")
		enable_product_sync()
		frappe.db.delete("CRM Product", {"product_code": ["like", "HOOK-%"]})
		frappe.db.delete("Item", {"item_code": ["like", "HOOK-%"]})

	def test_item_insert_creates_linked_crm_product(self):
		frappe.get_doc(
			{
				"doctype": "Item",
				"item_code": "HOOK-1",
				"item_name": "From ERP",
				"item_group": ITEM_GROUP,
				"standard_rate": 30,
			}
		).insert()
		self.assertTrue(frappe.db.exists("CRM Product", {"erpnext_item_code": "HOOK-1"}))
		self.assertEqual(frappe.db.get_value("Item", "HOOK-1", "crm_product_code"), "HOOK-1")

	def test_item_insert_syncs_to_crm_when_bidirectional_sync_is_off(self):
		set_bidirectional_product_sync(0)
		frappe.get_doc(
			{"doctype": "Item", "item_code": "HOOK-PULL", "item_name": "Pull", "item_group": ITEM_GROUP}
		).insert()
		self.assertTrue(frappe.db.exists("CRM Product", {"erpnext_item_code": "HOOK-PULL"}))

	def test_item_rename_updates_crm_product_link(self):
		frappe.get_doc(
			{"doctype": "Item", "item_code": "HOOK-2", "item_name": "X", "item_group": ITEM_GROUP}
		).insert()
		frappe.rename_doc("Item", "HOOK-2", "HOOK-2-NEW")
		self.assertEqual(
			frappe.db.get_value("CRM Product", {"erpnext_item_code": "HOOK-2-NEW"}, "erpnext_item_code"),
			"HOOK-2-NEW",
		)

	def test_item_delete_removes_linked_crm_product(self):
		frappe.get_doc(
			{"doctype": "Item", "item_code": "HOOK-3", "item_name": "Z", "item_group": ITEM_GROUP}
		).insert()
		self.assertTrue(frappe.db.exists("CRM Product", "HOOK-3"))
		# ERPNext is master: deleting the Item cascades to its linked CRM Product.
		frappe.delete_doc("Item", "HOOK-3")
		self.assertFalse(frappe.db.exists("CRM Product", "HOOK-3"))


class TestReconcileJob(FrappeTestCase):
	def setUp(self):
		if not frappe.db.exists("DocType", "Item"):
			self.skipTest("ERPNext not installed")
		enable_product_sync()
		frappe.db.delete("CRM Product", {"product_code": ["like", "JOB-%"]})
		frappe.db.delete("Item", {"item_code": ["like", "JOB-%"]})
		settings = frappe.get_single("ERPNext CRM Settings")
		settings.sync_issues = []
		settings.save(ignore_permissions=True)

	def test_unlinked_duplicates_get_linked(self):
		from crm.fcrm.doctype.crm_product.reconcile_job import run_reconciliation

		# Create an unlinked Item/Product pair (bypass the auto-sync hooks) so
		# reconciliation has duplicates to link.
		item = frappe.get_doc(
			{
				"doctype": "Item",
				"item_code": "JOB-A",
				"item_name": "Widget",
				"item_group": ITEM_GROUP,
				"standard_rate": 50,
			}
		)
		item.flags.ignore_crm_sync = True
		item.insert(ignore_permissions=True)
		product = frappe.get_doc(
			{"doctype": "CRM Product", "product_code": "JOB-A", "product_name": "Widget"}
		)
		product.flags.ignore_erpnext_sync = True
		product.insert(ignore_permissions=True)

		summary = run_reconciliation()
		self.assertEqual(summary["linked_by_exact_code"], 1)
		self.assertEqual(frappe.db.get_value("CRM Product", "JOB-A", "erpnext_item_code"), "JOB-A")
		self.assertEqual(frappe.db.get_value("Item", "JOB-A", "crm_product_code"), "JOB-A")
		self.assertEqual(frappe.db.get_value("CRM Product", "JOB-A", "standard_rate"), 50)

	def test_orphan_link_is_unlinked_and_recorded(self):
		from crm.fcrm.doctype.crm_product.reconcile_job import run_reconciliation

		product = frappe.get_doc(
			{
				"doctype": "CRM Product",
				"product_code": "JOB-ORPHAN",
				"product_name": "Orphan",
				"erpnext_item_code": "DELETED-ITEM",
			}
		)
		product.flags.ignore_erpnext_sync = True
		product.insert(ignore_permissions=True)
		run_reconciliation()
		self.assertIsNone(frappe.db.get_value("CRM Product", "JOB-ORPHAN", "erpnext_item_code"))
		issues = frappe.get_all(
			"CRM Product Sync Issue",
			filters={"parent": "ERPNext CRM Settings", "product": "JOB-ORPHAN"},
			fields=["kind"],
		)
		self.assertEqual(len(issues), 1)
		self.assertEqual(issues[0]["kind"], "unlinked_orphan")

	def test_skipped_when_cross_site(self):
		from crm.fcrm.doctype.crm_product.reconcile_job import run_reconciliation

		# Set the flag directly: saving the settings would trigger remote-site
		# custom-field creation, which is unrelated to what we're asserting here.
		self._set_cross_site(1)
		try:
			self.assertEqual(run_reconciliation(), {"skipped": "cross_site_not_supported"})
		finally:
			self._set_cross_site(0)

	@staticmethod
	def _set_cross_site(value):
		frappe.db.set_single_value("ERPNext CRM Settings", "is_erpnext_in_different_site", value)
		frappe.clear_document_cache("ERPNext CRM Settings", "ERPNext CRM Settings")


class TestCRMToERPNextCreate(FrappeTestCase):
	def setUp(self):
		if not frappe.db.exists("DocType", "Item"):
			self.skipTest("ERPNext not installed")
		enable_product_sync()
		frappe.db.delete("CRM Product", {"product_code": ["like", "PUSH-%"]})
		frappe.db.delete("Item", {"item_code": ["like", "PUSH-%"]})

	def test_direct_crm_product_creation_is_blocked(self):
		# ERPNext is the master: products must originate from an Item, not be created directly.
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(
				{"doctype": "CRM Product", "product_code": "PUSH-1", "product_name": "Pushed"}
			).insert()

	def test_reconciliation_creates_item_for_unlinked_product(self):
		from crm.fcrm.doctype.crm_product.reconcile_job import run_reconciliation

		product = frappe.get_doc(
			{"doctype": "CRM Product", "product_code": "PUSH-2", "product_name": "X", "standard_rate": 25}
		)
		product.flags.ignore_erpnext_sync = True
		product.insert(ignore_permissions=True)

		run_reconciliation()
		self.assertTrue(frappe.db.exists("Item", "PUSH-2"))
		self.assertEqual(frappe.db.get_value("Item", "PUSH-2", "standard_rate"), 25)
		self.assertEqual(frappe.db.get_value("Item", "PUSH-2", "crm_product_code"), "PUSH-2")
		self.assertEqual(frappe.db.get_value("CRM Product", "PUSH-2", "erpnext_item_code"), "PUSH-2")

	def test_reconciliation_does_not_create_item_when_bidirectional_sync_is_off(self):
		from crm.fcrm.doctype.crm_product.reconcile_job import run_reconciliation

		set_bidirectional_product_sync(0)
		frappe.get_doc({"doctype": "CRM Product", "product_code": "PUSH-OFF", "product_name": "Off"}).insert()

		run_reconciliation()
		self.assertFalse(frappe.db.exists("Item", "PUSH-OFF"))

	def test_update_to_linked_product_pushes_to_item(self):
		from crm.fcrm.doctype.crm_product.reconcile_job import run_reconciliation

		product = frappe.get_doc(
			{"doctype": "CRM Product", "product_code": "PUSH-3", "product_name": "Y", "standard_rate": 10}
		)
		product.flags.ignore_erpnext_sync = True
		product.insert(ignore_permissions=True)
		run_reconciliation()  # creates and links Item PUSH-3

		p = frappe.get_doc("CRM Product", "PUSH-3")
		p.standard_rate = 99
		p.save()
		self.assertEqual(frappe.db.get_value("Item", "PUSH-3", "standard_rate"), 99)


class TestUserPermissionMirror(FrappeTestCase):
	def setUp(self):
		if not frappe.db.exists("DocType", "Item"):
			self.skipTest("ERPNext not installed")
		enable_product_sync()
		frappe.db.delete("User Permission", {"for_value": ["like", "PERM-%"]})
		frappe.db.delete("CRM Product", {"product_code": ["like", "PERM-%"]})
		frappe.db.delete("Item", {"item_code": ["like", "PERM-%"]})
		frappe.get_doc(
			{"doctype": "Item", "item_code": "PERM-1", "item_name": "P", "item_group": ITEM_GROUP}
		).insert(ignore_permissions=True)

	def test_user_permission_on_item_mirrors_to_crm_product(self):
		frappe.get_doc(
			{
				"doctype": "User Permission",
				"user": "Administrator",
				"allow": "Item",
				"for_value": "PERM-1",
				"apply_to_all_doctypes": 1,
			}
		).insert(ignore_permissions=True)
		self.assertTrue(
			frappe.db.exists(
				"User Permission",
				{"user": "Administrator", "allow": "CRM Product", "for_value": "PERM-1"},
			)
		)

	def test_user_permission_on_crm_product_mirrors_to_item(self):
		frappe.get_doc(
			{
				"doctype": "User Permission",
				"user": "Administrator",
				"allow": "CRM Product",
				"for_value": "PERM-1",
				"apply_to_all_doctypes": 1,
			}
		).insert(ignore_permissions=True)
		self.assertTrue(
			frappe.db.exists(
				"User Permission",
				{"user": "Administrator", "allow": "Item", "for_value": "PERM-1"},
			)
		)

	def test_delete_user_permission_deletes_mirror(self):
		p = frappe.get_doc(
			{
				"doctype": "User Permission",
				"user": "Administrator",
				"allow": "Item",
				"for_value": "PERM-1",
				"apply_to_all_doctypes": 1,
			}
		).insert(ignore_permissions=True)
		p.delete(ignore_permissions=True)
		self.assertFalse(
			frappe.db.exists(
				"User Permission",
				{"user": "Administrator", "allow": "CRM Product", "for_value": "PERM-1"},
			)
		)


class TestDocShareMirror(FrappeTestCase):
	def setUp(self):
		if not frappe.db.exists("DocType", "Item"):
			self.skipTest("ERPNext not installed")
		enable_product_sync()
		frappe.db.delete("DocShare", {"share_name": ["like", "SHARE-%"]})
		frappe.db.delete("CRM Product", {"product_code": ["like", "SHARE-%"]})
		frappe.db.delete("Item", {"item_code": ["like", "SHARE-%"]})
		frappe.get_doc(
			{"doctype": "Item", "item_code": "SHARE-1", "item_name": "S", "item_group": ITEM_GROUP}
		).insert(ignore_permissions=True)

	def test_share_on_item_mirrors_to_crm_product(self):
		frappe.get_doc(
			{
				"doctype": "DocShare",
				"user": "Administrator",
				"share_doctype": "Item",
				"share_name": "SHARE-1",
				"read": 1,
			}
		).insert(ignore_permissions=True)
		self.assertTrue(
			frappe.db.exists(
				"DocShare",
				{"user": "Administrator", "share_doctype": "CRM Product", "share_name": "SHARE-1"},
			)
		)

	def test_delete_share_deletes_mirror(self):
		s = frappe.get_doc(
			{
				"doctype": "DocShare",
				"user": "Administrator",
				"share_doctype": "Item",
				"share_name": "SHARE-1",
				"read": 1,
			}
		).insert(ignore_permissions=True)
		s.delete(ignore_permissions=True)
		self.assertFalse(
			frappe.db.exists(
				"DocShare",
				{"user": "Administrator", "share_doctype": "CRM Product", "share_name": "SHARE-1"},
			)
		)


class TestDeleteGuard(FrappeTestCase):
	def test_cannot_delete_crm_product_with_referenced_item(self):
		if not frappe.db.exists("DocType", "Quotation"):
			self.skipTest("ERPNext not installed")
		if not frappe.db.exists("Customer", "_Test Customer"):
			self.skipTest("ERPNext transactional test data not set up")
		company = frappe.defaults.get_global_default("company") or frappe.db.get_value("Company", {}, "name")
		if not company:
			self.skipTest("No ERPNext company available")
		enable_product_sync()
		frappe.db.delete("CRM Product", {"product_code": "DEL-1"})
		frappe.db.delete("Item", {"item_code": "DEL-1"})
		# Create via the Item so the linked CRM Product is generated by the integration.
		frappe.get_doc(
			{"doctype": "Item", "item_code": "DEL-1", "item_name": "X", "item_group": ITEM_GROUP}
		).insert(ignore_permissions=True)
		# Set currency explicitly: a fresh ERPNext test site has no Price List to derive it from.
		quotation = frappe.get_doc(
			{
				"doctype": "Quotation",
				"quotation_to": "Customer",
				"party_name": "_Test Customer",
				"company": company,
				"currency": frappe.db.get_value("Company", company, "default_currency"),
				"conversion_rate": 1,
				"items": [{"item_code": "DEL-1", "qty": 1, "rate": 10}],
			}
		)
		quotation.flags.ignore_price_list = True
		quotation.insert(ignore_permissions=True)
		with self.assertRaises(frappe.ValidationError):
			frappe.delete_doc("CRM Product", "DEL-1")
