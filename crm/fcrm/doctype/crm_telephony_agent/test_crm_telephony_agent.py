# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase

AGENT_USER = "telephony-agent@example.com"


class IntegrationTestCRMTelephonyAgent(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		if not frappe.db.exists("User", AGENT_USER):
			frappe.get_doc(
				{"doctype": "User", "email": AGENT_USER, "first_name": "Agent", "send_welcome_email": 0}
			).insert(ignore_permissions=True)

	def setUp(self):
		frappe.delete_doc_if_exists("CRM Telephony Agent", AGENT_USER)
		self.agent = frappe.get_doc(
			{"doctype": "CRM Telephony Agent", "user": AGENT_USER, "mobile_no": "+911111111111"}
		).insert(ignore_permissions=True)

	def test_a_new_mobile_no_becomes_the_only_primary_number(self):
		self.agent.mobile_no = "+912222222222"
		self.agent.save(ignore_permissions=True)

		self.assertEqual(self.agent.mobile_no, "+912222222222")
		self.assertEqual(self.numbers(), [("+912222222222", 1)])

	def test_a_mobile_no_already_listed_becomes_primary(self):
		self.agent.append("phone_nos", {"number": "+912222222222"})
		self.agent.save(ignore_permissions=True)

		self.agent.mobile_no = "+912222222222"
		self.agent.save(ignore_permissions=True)

		self.assertEqual(self.agent.mobile_no, "+912222222222")
		self.assertEqual(self.numbers(), [("+912222222222", 1)])

	def test_a_mobile_no_that_is_not_a_phone_number_is_refused(self):
		self.agent.mobile_no = "call me maybe"
		self.assertRaises(frappe.InvalidPhoneNumberError, self.agent.save, ignore_permissions=True)

	def numbers(self):
		return [(phone.number, phone.is_primary) for phone in self.agent.phone_nos]
