# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

from frappe.tests import IntegrationTestCase

from crm.api.session import get_user_info


class TestSession(IntegrationTestCase):
	def test_get_user_info_finds_a_user_by_email(self):
		from frappe.core.doctype.user.test_user import test_user

		with test_user(roles=["Sales User"], generated_id=True) as user:
			info = get_user_info([user.email])

		self.assertEqual([row.name for row in info], [user.name])
