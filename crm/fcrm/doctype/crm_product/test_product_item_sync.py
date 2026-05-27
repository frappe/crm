import frappe
from frappe.tests.utils import FrappeTestCase


class TestReverseLinkField(FrappeTestCase):
	def test_item_has_crm_product_code_field(self):
		if not frappe.db.exists("DocType", "Item"):
			self.skipTest("ERPNext not installed")
		from crm.patches.v1_0.create_custom_fields_for_product_item_sync import execute

		execute()
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
		from crm.fcrm.doctype.crm_product.sync_utils import same_site_sync_active

		if not same_site_sync_active():
			self.skipTest("Integration not enabled or cross-site")
		frappe.db.delete("CRM Product", {"product_code": ["like", "HOOK-%"]})
		frappe.db.delete("Item", {"item_code": ["like", "HOOK-%"]})

	def test_item_insert_creates_linked_crm_product(self):
		frappe.get_doc(
			{
				"doctype": "Item",
				"item_code": "HOOK-1",
				"item_name": "From ERP",
				"standard_rate": 30,
			}
		).insert()
		self.assertTrue(frappe.db.exists("CRM Product", {"erpnext_item_code": "HOOK-1"}))
		self.assertEqual(frappe.db.get_value("Item", "HOOK-1", "crm_product_code"), "HOOK-1")

	def test_item_rename_updates_crm_product_link(self):
		frappe.get_doc({"doctype": "Item", "item_code": "HOOK-2", "item_name": "X"}).insert()
		frappe.rename_doc("Item", "HOOK-2", "HOOK-2-NEW")
		self.assertEqual(
			frappe.db.get_value("CRM Product", {"erpnext_item_code": "HOOK-2-NEW"}, "erpnext_item_code"),
			"HOOK-2-NEW",
		)

	def test_item_delete_removes_link_on_crm_product(self):
		frappe.get_doc({"doctype": "Item", "item_code": "HOOK-3", "item_name": "Z"}).insert()
		frappe.delete_doc("Item", "HOOK-3")
		product = frappe.db.get_value(
			"CRM Product", {"product_code": "HOOK-3"}, ["erpnext_item_code"], as_dict=True
		)
		self.assertIsNone(product.erpnext_item_code)


class TestReconcileJob(FrappeTestCase):
	def setUp(self):
		if not frappe.db.exists("DocType", "Item"):
			self.skipTest("ERPNext not installed")
		frappe.db.delete("CRM Product", {"product_code": ["like", "JOB-%"]})
		frappe.db.delete("Item", {"item_code": ["like", "JOB-%"]})
		settings = frappe.get_single("ERPNext CRM Settings")
		settings.sync_issues = []
		settings.save(ignore_permissions=True)

	def test_unlinked_duplicates_get_linked(self):
		from crm.fcrm.doctype.crm_product.reconcile_job import run_reconciliation

		frappe.get_doc(
			{
				"doctype": "Item",
				"item_code": "JOB-A",
				"item_name": "Widget",
				"standard_rate": 50,
			}
		).insert(ignore_permissions=True)
		frappe.get_doc({"doctype": "CRM Product", "product_code": "JOB-A", "product_name": "Widget"}).insert(
			ignore_permissions=True
		)

		summary = run_reconciliation()
		self.assertEqual(summary["linked_by_exact_code"], 1)
		self.assertEqual(frappe.db.get_value("CRM Product", "JOB-A", "erpnext_item_code"), "JOB-A")
		self.assertEqual(frappe.db.get_value("Item", "JOB-A", "crm_product_code"), "JOB-A")
		self.assertEqual(frappe.db.get_value("CRM Product", "JOB-A", "standard_rate"), 50)

	def test_orphan_link_is_unlinked_and_recorded(self):
		from crm.fcrm.doctype.crm_product.reconcile_job import run_reconciliation

		frappe.get_doc(
			{
				"doctype": "CRM Product",
				"product_code": "JOB-ORPHAN",
				"product_name": "Orphan",
				"erpnext_item_code": "DELETED-ITEM",
			}
		).insert(ignore_permissions=True)
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

		settings = frappe.get_single("ERPNext CRM Settings")
		settings.is_erpnext_in_different_site = 1
		settings.save(ignore_permissions=True)
		try:
			self.assertEqual(run_reconciliation(), {"skipped": "cross_site_not_supported"})
		finally:
			settings.is_erpnext_in_different_site = 0
			settings.save(ignore_permissions=True)


class TestCRMToERPNextCreate(FrappeTestCase):
	def setUp(self):
		if not frappe.db.exists("DocType", "Item"):
			self.skipTest("ERPNext not installed")
		frappe.db.delete("CRM Product", {"product_code": ["like", "PUSH-%"]})
		frappe.db.delete("Item", {"item_code": ["like", "PUSH-%"]})

	def test_inserting_crm_product_creates_item(self):
		p = frappe.get_doc(
			{
				"doctype": "CRM Product",
				"product_code": "PUSH-1",
				"product_name": "Pushed",
				"standard_rate": 25,
			}
		).insert()
		self.assertEqual(p.erpnext_item_code, "PUSH-1")
		self.assertTrue(frappe.db.exists("Item", "PUSH-1"))
		self.assertEqual(frappe.db.get_value("Item", "PUSH-1", "standard_rate"), 25)
		self.assertEqual(frappe.db.get_value("Item", "PUSH-1", "crm_product_code"), "PUSH-1")

	def test_update_crm_product_updates_item(self):
		p = frappe.get_doc(
			{
				"doctype": "CRM Product",
				"product_code": "PUSH-2",
				"product_name": "X",
				"standard_rate": 10,
			}
		).insert()
		p.standard_rate = 99
		p.save()
		self.assertEqual(frappe.db.get_value("Item", "PUSH-2", "standard_rate"), 99)


class TestUserPermissionMirror(FrappeTestCase):
	def setUp(self):
		if not frappe.db.exists("DocType", "Item"):
			self.skipTest("ERPNext not installed")
		from crm.integrations.erpnext.utils import should_sync

		if not should_sync():
			self.skipTest("Integration not enabled")
		frappe.db.delete("User Permission", {"for_value": ["like", "PERM-%"]})
		frappe.db.delete("CRM Product", {"product_code": ["like", "PERM-%"]})
		frappe.db.delete("Item", {"item_code": ["like", "PERM-%"]})
		frappe.get_doc({"doctype": "Item", "item_code": "PERM-1", "item_name": "P"}).insert(
			ignore_permissions=True
		)

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
		from crm.integrations.erpnext.utils import should_sync

		if not should_sync():
			self.skipTest("Integration not enabled")
		frappe.db.delete("DocShare", {"share_name": ["like", "SHARE-%"]})
		frappe.db.delete("CRM Product", {"product_code": ["like", "SHARE-%"]})
		frappe.db.delete("Item", {"item_code": ["like", "SHARE-%"]})
		frappe.get_doc({"doctype": "Item", "item_code": "SHARE-1", "item_name": "S"}).insert(
			ignore_permissions=True
		)

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
		frappe.db.delete("CRM Product", {"product_code": "DEL-1"})
		frappe.db.delete("Item", {"item_code": "DEL-1"})
		frappe.get_doc({"doctype": "CRM Product", "product_code": "DEL-1", "product_name": "X"}).insert()
		frappe.get_doc(
			{
				"doctype": "Quotation",
				"quotation_to": "Customer",
				"party_name": "_Test Customer",
				"items": [{"item_code": "DEL-1", "qty": 1, "rate": 10}],
			}
		).insert(ignore_permissions=True)
		with self.assertRaises(frappe.ValidationError):
			frappe.delete_doc("CRM Product", "DEL-1")
