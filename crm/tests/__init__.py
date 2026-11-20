import functools
import json
import os
import unittest

import frappe


def before_tests():
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


def requires_whatsapp(test):
	"""Skip a test case or a test on a site without the optional whatsapp app."""
	if isinstance(test, type):
		test.setUp = requires_whatsapp(test.setUp)
		return test

	@functools.wraps(test)
	def run_with_whatsapp(*args, **kwargs):
		if "whatsapp" not in frappe.get_installed_apps():
			raise unittest.SkipTest("WhatsApp is not installed")
		return test(*args, **kwargs)

	return run_with_whatsapp
