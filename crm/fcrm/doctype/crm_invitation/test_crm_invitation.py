# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, now

from crm.permissions.test_org_hierarchy import make_user


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

	def test_desk_accept_mails_new_user_a_set_password_link(self):
		invitation = self.make_invitation(email="desk-invitee@example.com")

		with patch("frappe.core.doctype.user.user.User.send_welcome_mail_to_user") as welcome_mail:
			invitation.accept_invitation()

		welcome_mail.assert_called_once()

	def test_desk_accept_does_not_mail_existing_user(self):
		frappe.get_doc(
			doctype="User",
			user_type="System User",
			email="desk-existing@example.com",
			send_welcome_email=0,
			first_name="Desk Existing",
		).insert(ignore_permissions=True)
		invitation = self.make_invitation(email="desk-existing@example.com")

		with patch("frappe.core.doctype.user.user.User.send_welcome_mail_to_user") as welcome_mail:
			invitation.accept_invitation()

		welcome_mail.assert_not_called()

	def test_expire_invitations_expires_old_pending_invites(self):
		from crm.fcrm.doctype.crm_invitation.crm_invitation import expire_invitations

		invitation = self.make_invitation(email="stale@example.com")
		frappe.db.set_value(
			"CRM Invitation", invitation.name, "creation", add_days(now(), -4), update_modified=False
		)

		expire_invitations()

		self.assertEqual(frappe.db.get_value("CRM Invitation", invitation.name, "status"), "Expired")

	def test_accept_grants_role_to_user(self):
		invitation = self.make_invitation(email="manager@example.com", role="Sales Manager")

		invitation.accept()

		user = frappe.get_doc("User", invitation.email)
		user_roles = {r.role for r in user.roles}
		self.assertIn("Sales Manager", user_roles)
		self.assertIn("Sales User", user_roles)

	def set_sales_manager(self):
		frappe.set_user(make_user("invitation.manager@example.com", ["Sales Manager"]).name)
		self.addCleanup(frappe.set_user, "Administrator")

	def test_sales_manager_can_only_invite_sales_users(self):
		self.set_sales_manager()

		for role in ("System Manager", "Sales Manager"):
			with self.assertRaises(frappe.PermissionError):
				self.insert_as_session_user(email=f"{role.split()[0].lower()}@example.com", role=role)

		invitation = self.insert_as_session_user(email="sales.user@example.com", role="Sales User")
		self.assertTrue(frappe.db.get_value("CRM Invitation", invitation.name, "key"))

	def test_system_manager_can_invite_any_role(self):
		for role in ("System Manager", "Sales Manager", "Sales User"):
			invitation = self.insert_as_session_user(
				email=f"{role.split()[0].lower()}@example.com", role=role
			)
			self.assertTrue(invitation.key)

	def test_role_and_email_cannot_change_after_insert(self):
		invitation = self.make_invitation(email="sales.user@example.com")
		self.set_sales_manager()

		invitation = frappe.get_doc("CRM Invitation", invitation.name)
		invitation.role = "System Manager"
		with self.assertRaises(frappe.CannotChangeConstantError):
			invitation.save()

		invitation.reload()
		invitation.email = "other@example.com"
		with self.assertRaises(frappe.CannotChangeConstantError):
			invitation.save()

	def test_key_is_only_exposed_through_the_invite(self):
		from frappe.client import get as client_get

		invitation = self.make_invitation(email="sales.user@example.com")
		key = invitation.key
		self.set_sales_manager()

		self.assertNotIn("key", client_get("CRM Invitation", invitation.name))

		doc = frappe.get_doc("CRM Invitation", invitation.name)
		doc.key = "changed"
		doc.save()
		self.assertEqual(frappe.db.get_value("CRM Invitation", invitation.name, "key"), key)

	def test_guest_can_accept_system_manager_invite(self):
		from crm.api import accept_invitation

		invitation = self.make_invitation(email="admin.invitee@example.com", role="System Manager")
		frappe.set_user("Guest")
		self.addCleanup(frappe.set_user, "Administrator")

		accept_invitation(key=invitation.key)

		frappe.set_user("Administrator")
		self.assertEqual(frappe.db.get_value("CRM Invitation", invitation.name, "status"), "Accepted")

	def insert_as_session_user(self, email, role):
		with patch.object(frappe, "sendmail"):
			return frappe.get_doc(doctype="CRM Invitation", email=email, role=role).insert()
