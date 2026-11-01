# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from crm.fcrm.doctype.erpnext_crm_settings.erpnext_crm_settings import get_product_sync_status

SYNC_COLUMNS = {("CRM Product", "erpnext_item_code"), ("Item", "crm_product_code")}


class TestERPNextCRMSettings(IntegrationTestCase):
	def test_product_sync_status_without_the_integration_custom_fields(self):
		real_has_column = frappe.db.has_column
		queried = []
		real_get_all, real_count = frappe.get_all, frappe.db.count

		def has_column(doctype, column):
			return (doctype, column) not in SYNC_COLUMNS and real_has_column(doctype, column)

		def get_all(doctype, *args, **kwargs):
			queried.append((doctype, kwargs.get("fields"), kwargs.get("filters")))
			return real_get_all(doctype, *args, **kwargs)

		def count(doctype, *args, **kwargs):
			queried.append((doctype, None, kwargs.get("filters")))
			return real_count(doctype, *args, **kwargs)

		with (
			patch.object(frappe.db, "has_column", has_column),
			patch.object(frappe, "get_all", get_all),
			patch.object(frappe.db, "count", count),
		):
			status = get_product_sync_status()

		for query in queried:
			self.assertNotIn("erpnext_item_code", str(query))
			self.assertNotIn("crm_product_code", str(query))
		assert status["unsynced"]["products"] == 0
		assert status["unsynced"]["items"] == 0
		assert status["items"] == {"count": 0, "rows": []}
		assert all("erpnext_item_code" not in row for row in status["products"]["rows"])

	def test_product_sync_status_reads_the_custom_fields_when_they_exist(self):
		product = frappe._dict(name="P-1", product_code="P-1", product_name="One", erpnext_item_code="ITEM-1")
		synced_item = frappe._dict(name="ITEM-1", item_code="ITEM-1", crm_product_code="P-1")
		rows = {
			"CRM Product": [product],
			"Item": [synced_item],
		}
		requested = []

		def get_all(doctype, *args, **kwargs):
			requested.append((doctype, kwargs.get("fields")))
			if doctype == "Item" and kwargs["fields"] == ["name", "item_group"]:
				return [frappe._dict(name="ITEM-1", item_group="Services")]
			return rows[doctype]

		with (
			patch.object(frappe.db, "has_column", return_value=True),
			patch.object(frappe.db, "exists", return_value=True),
			patch.object(frappe, "has_permission", return_value=True),
			patch.object(frappe, "get_all", get_all),
			patch.object(frappe.db, "count", return_value=3),
		):
			status = get_product_sync_status()

		assert ("CRM Product", ["name", "product_code", "product_name", "erpnext_item_code"]) in requested
		assert status["products"] == {"count": 3, "rows": [product]}
		assert status["products"]["rows"][0]["item_group"] == "Services"
		assert status["items"] == {"count": 3, "rows": [synced_item]}
		assert status["unsynced"]["products"] == 3
		assert status["unsynced"]["items"] == 3
