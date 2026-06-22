import json
import os

import frappe


def before_tests():
	# When ERPNext is installed (integration CI), creating Company test records
	# triggers default account/warehouse setup, which needs setup-wizard fixtures
	# (e.g. the "Transit" Warehouse Type) that a bare install-app does not create.
	# CRM tests never exercise that accounting setup, so skip it.
	if frappe.db.exists("DocType", "Company"):
		frappe.flags.ignore_chart_of_accounts = True

	load_crm_user_test_records()


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
