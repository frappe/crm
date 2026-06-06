# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase, UnitTestCase

# On IntegrationTestCase, the doctype test records and all
# link-field test record dependencies are recursively loaded
# Use these module variables to add/remove to/from that list
EXTRA_TEST_RECORD_DEPENDENCIES = []  # eg. ["User"]
IGNORE_TEST_RECORD_DEPENDENCIES = []  # eg. ["User"]


class UnitTestAnTekIntegrationSettings(UnitTestCase):
	"""
	Unit tests for AnTekIntegrationSettings.
	Use this class for testing individual functions and methods.
	"""

	pass


class IntegrationTestAnTekIntegrationSettings(IntegrationTestCase):
	"""
	Integration tests for AnTekIntegrationSettings.
	Use this class for testing interactions between multiple components.
	"""

	def test_singleton_has_default_timeout(self):
		doc = frappe.get_single("AnTek Integration Settings")
		self.assertEqual(doc.request_timeout_seconds, 5)
