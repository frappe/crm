import json
import os

import frappe

# Version-aware base test case: frappe v16 ships IntegrationTestCase (which avoids
# the legacy compat preload that imports erpnext's heavy test bootstrap); v15 only
# has FrappeTestCase. Tests import CRMTestCase so the same suite runs on both.
try:
	from frappe.tests import IntegrationTestCase as CRMTestCase
except ImportError:
	from frappe.tests.utils import FrappeTestCase as CRMTestCase


def before_tests():
	# In integration CI ERPNext is installed via `install-app`, which does not run
	# the setup wizard. So the root fixtures the product-sync tests rely on
	# (Item Group "All Item Groups", UOM "Nos", Warehouse Type "Transit", ...) are
	# missing and Item/Company test records fail. Bootstrap them once here.
	if frappe.db.exists("DocType", "Company"):
		# Skip the heavy default account/warehouse setup on Company test records;
		# CRM tests never exercise ERPNext accounting.
		frappe.flags.ignore_chart_of_accounts = True
		ensure_erpnext_fixtures()

	load_crm_user_test_records()


def ensure_erpnext_fixtures():
	"""Create ERPNext setup-wizard fixtures the integration tests rely on."""
	if not frappe.db.exists("Item Group", "All Item Groups"):
		from erpnext.setup.setup_wizard.operations.install_fixtures import install

		# A country is required: install() builds a root Territory named after it.
		install("India")

	# Item defaults stock_uom from the global default ERPNext normally sets when
	# Stock Settings is saved; a bare install never sets it (UOM "Nos" is created
	# by install_fixtures above), so set the default directly.
	if not frappe.db.get_default("stock_uom"):
		frappe.db.set_default("stock_uom", "Nos")


def load_crm_user_test_records():
	"""Load CRM user test records from crm/tests/test_records.json"""
	test_records_path = os.path.join(os.path.dirname(__file__), "test_records.json")

	if os.path.exists(test_records_path):
		with open(test_records_path) as f:
			test_records = json.load(f)

		for record in test_records:
			if not frappe.db.exists("User", record.get("email")):
				doc = frappe.get_doc(record)
				doc.insert(ignore_permissions=True, ignore_if_duplicate=True)
