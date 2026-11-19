# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase

from crm.automation.reference_flows import assign_step, email_step


class TestReferenceFlows(IntegrationTestCase):
	def test_steps_name_people_by_user_id(self):
		from frappe.core.doctype.user.test_user import test_user

		with test_user(roles=["Sales User"], generated_id=True) as user:
			assign = frappe.parse_json(assign_step(1, "assign", user.email, "Call them")["params"])
			email = frappe.parse_json(
				email_step(2, "email", "CRM Lead Follow Up", sender=user.email)["params"]
			)

		self.assertEqual(assign["assign_to"], [user.name])
		self.assertEqual(email["sender"], user.name)
