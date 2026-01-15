# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

# import frappe
<<<<<<< HEAD
from frappe.tests.utils import FrappeTestCase
=======
from frappe.tests import IntegrationTestCase
>>>>>>> 6297a08d (chore: linter fixes)

# On IntegrationTestCase, the doctype test records and all
# link-field test record dependencies are recursively loaded
# Use these module variables to add/remove to/from that list
EXTRA_TEST_RECORD_DEPENDENCIES = []  # eg. ["User"]
IGNORE_TEST_RECORD_DEPENDENCIES = []  # eg. ["User"]


<<<<<<< HEAD
class TestFailedLeadSyncLog(FrappeTestCase):
=======
class IntegrationTestFailedLeadSyncLog(IntegrationTestCase):
>>>>>>> 6297a08d (chore: linter fixes)
	"""
	Integration tests for FailedLeadSyncLog.
	Use this class for testing interactions between multiple components.
	"""

	pass
