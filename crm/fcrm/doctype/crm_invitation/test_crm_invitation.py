# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase


class TestCRMInvitation(FrappeTestCase):
	def make_invitation(self, email="invitee@example.com", role="Sales User"):
		"""Create a Pending invitation without actually sending an email."""
		with patch.object(frappe, "sendmail"):
			return frappe.get_doc(
				doctype="CRM Invitation",
				email=email,
				role=role,
			).insert(ignore_permissions=True)

	def test_new_invitation_is_pending_with_key(self):
		invitation = self.make_invitation()
		self.assertEqual(invitation.status, "Pending")
		self.assertTrue(invitation.key)
		self.assertEqual(invitation.invited_by, frappe.session.user)

	def test_accept_pending_invitation(self):
		invitation = self.make_invitation()

		invitation.accept()

		self.assertEqual(invitation.status, "Accepted")
		self.assertTrue(invitation.accepted_at)
		self.assertTrue(frappe.db.exists("User", invitation.email))

	def test_accept_clears_key(self):
		"""The key is wiped after acceptance so the invite link cannot be reused."""
		invitation = self.make_invitation()

		invitation.accept()

		self.assertIsNone(invitation.key)
		self.assertFalse(frappe.db.get_value("CRM Invitation", invitation.name, "key"))

	def test_accept_already_accepted_raises(self):
		"""An already-accepted invitation cannot be accepted again."""
		invitation = self.make_invitation()
		invitation.accept()

		invitation.reload()
		with self.assertRaises(frappe.ValidationError):
			invitation.accept()

	def test_accept_expired_invitation_raises(self):
		invitation = self.make_invitation()
		invitation.status = "Expired"
		invitation.save(ignore_permissions=True)

		with self.assertRaises(frappe.ValidationError):
			invitation.accept()

	def test_accept_reports_newly_created_user(self):
		invitation = self.make_invitation(email="brand-new@example.com")

		self.assertTrue(invitation.accept())
		self.assertEqual(frappe.db.get_value("User", invitation.email, "default_app"), "crm")

	def test_accept_reports_existing_user(self):
		frappe.get_doc(
			doctype="User",
			user_type="System User",
			email="already-there@example.com",
			send_welcome_email=0,
			first_name="Already There",
		).insert(ignore_permissions=True)
		invitation = self.make_invitation(email="already-there@example.com")

		self.assertFalse(invitation.accept())

	def test_accept_invitation_sends_new_user_to_set_password(self):
		"""A new user must set a password instead of being logged in directly."""
		from crm.api import accept_invitation

		invitation = self.make_invitation(email="new-invitee@example.com")

		accept_invitation(key=invitation.key)

		self.assertEqual(frappe.local.response["type"], "redirect")
		self.assertIn("/update-password?key=", frappe.local.response["location"])

	def test_accept_invitation_logs_in_existing_user(self):
		"""An existing user already has a password, so log them straight in."""
		from crm.api import accept_invitation

		frappe.get_doc(
			doctype="User",
			user_type="System User",
			email="existing-invitee@example.com",
			send_welcome_email=0,
			first_name="Existing Invitee",
		).insert(ignore_permissions=True)
		invitation = self.make_invitation(email="existing-invitee@example.com")

		with patch.object(frappe.local, "login_manager", create=True) as login_manager:
			accept_invitation(key=invitation.key)

		login_manager.login_as.assert_called_once_with("existing-invitee@example.com")
		self.assertEqual(frappe.local.response["location"], "/crm")

	def test_accept_grants_role_to_user(self):
		invitation = self.make_invitation(email="manager@example.com", role="Sales Manager")

		invitation.accept()

		user = frappe.get_doc("User", invitation.email)
		user_roles = {r.role for r in user.roles}
		self.assertIn("Sales Manager", user_roles)
		self.assertIn("Sales User", user_roles)
