import json
import os

import frappe


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
	"""Create ERPNext's standard setup-wizard fixtures needed by integration tests."""
	if frappe.db.exists("Item Group", "All Item Groups"):
		return
	from erpnext.setup.setup_wizard.operations.install_fixtures import install

	install()


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
