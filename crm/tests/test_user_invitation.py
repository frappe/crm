# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

from unittest.mock import patch

import frappe
from frappe.core.api.user_invitation import invite_by_email
from frappe.core.doctype.user_invitation.user_invitation import UserInvitation
from frappe.tests import IntegrationTestCase

from crm.tests.test_password_setup import make_user

INVITEE = "invite-new@example.com"


class TestUserInvitation(IntegrationTestCase):
	def setUp(self):
		self.admin = make_user("invite-admin@example.com", roles=["System Manager"])
		self.manager = make_user("invite-manager@example.com", roles=["Sales Manager", "Sales User"])
		self.rep = make_user("invite-rep@example.com", roles=["Sales User"])
		mail = patch.object(UserInvitation, "send_invitation_mail")
		mail.start()
		self.addCleanup(mail.stop)

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def test_a_sales_manager_invites_a_sales_user_who_lands_with_that_role(self):
		frappe.set_user(self.manager.name)
		result = invite(["Sales User"])

		self.assertEqual(result["invited_emails"], [INVITEE])
		user = accept()
		self.assertIn("Sales User", frappe.get_roles(INVITEE))
		self.assertNotIn("Sales Manager", frappe.get_roles(INVITEE))
		self.assertTrue(user.block_modules)
		self.assertNotIn("FCRM", [row.module for row in user.block_modules])

	def test_a_sales_manager_may_not_invite_a_system_manager(self):
		frappe.set_user(self.manager.name)

		with self.assertRaises(frappe.ValidationError):
			invite(["System Manager"])
		self.assertFalse(frappe.db.exists("User Invitation", {"email": INVITEE}))

	def test_a_sales_manager_may_not_invite_a_sales_manager(self):
		frappe.set_user(self.manager.name)

		with self.assertRaises(frappe.ValidationError):
			invite(["Sales Manager"])

	def test_a_system_manager_invitee_gets_the_crm_roles_below_it(self):
		frappe.set_user(self.admin.name)
		invite(["System Manager"])

		user = accept()
		self.assertTrue({"System Manager", "Sales Manager", "Sales User"} <= set(frappe.get_roles(INVITEE)))
		self.assertFalse(user.block_modules)

	def test_an_existing_manager_invited_as_sales_user_keeps_their_roles(self):
		make_user(INVITEE, roles=["Sales Manager", "Sales User"])
		frappe.set_user(self.manager.name)
		invite(["Sales User"])

		user = accept()
		self.assertIn("Sales Manager", frappe.get_roles(INVITEE))
		self.assertFalse(user.block_modules)

	def test_a_sales_user_may_not_invite(self):
		frappe.set_user(self.rep.name)

		with self.assertRaises(frappe.PermissionError):
			invite(["Sales User"])


def invite(roles):
	return invite_by_email(emails=INVITEE, roles=roles, redirect_to_path="/apps/crm", app_name="crm")


def accept():
	frappe.get_last_doc("User Invitation", {"email": INVITEE}).accept(ignore_permissions=True)
	return frappe.get_doc("User", INVITEE)
