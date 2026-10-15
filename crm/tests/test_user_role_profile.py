# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase

from crm.api.user import add_existing_users, remove_crm_roles_from_user, update_user_role

ROLE_PROFILE = "_Test CRM Sales User Only"


def make_user(email, role_profile=None):
	user = frappe.get_doc(
		doctype="User",
		user_type="System User",
		email=email,
		first_name=email.split("@")[0].title(),
		send_welcome_email=0,
	).insert(ignore_permissions=True)

	if role_profile:
		user.append("role_profiles", {"role_profile": role_profile})
		user.save(ignore_permissions=True)

	return user


def user_roles(email):
	return {d.role for d in frappe.get_doc("User", email).roles}


class TestUserRoleProfile(IntegrationTestCase):
	"""Role changes must not be silently reverted by an assigned Role Profile (#2321)."""

	def setUp(self):
		frappe.set_user("Administrator")
		if not frappe.db.exists("Role Profile", ROLE_PROFILE):
			frappe.get_doc(
				doctype="Role Profile",
				role_profile=ROLE_PROFILE,
				roles=[{"role": "Sales User"}],
			).insert(ignore_permissions=True)

		self.profiled = make_user("role-profile@example.com", role_profile=ROLE_PROFILE)
		self.plain = make_user("no-role-profile@example.com")

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def test_update_role_throws_when_role_profile_assigned(self):
		self.assertEqual(user_roles(self.profiled.name) & {"Sales User", "Sales Manager"}, {"Sales User"})

		with self.assertRaises(frappe.ValidationError):
			update_user_role(self.profiled.name, "Sales Manager")

		self.assertNotIn("Sales Manager", user_roles(self.profiled.name))

	def test_add_existing_users_throws_when_role_profile_assigned(self):
		with self.assertRaises(frappe.ValidationError):
			add_existing_users([self.profiled.name], "Sales Manager")

		self.assertNotIn("Sales Manager", user_roles(self.profiled.name))

	def test_remove_throws_when_role_profile_assigned(self):
		with self.assertRaises(frappe.ValidationError):
			remove_crm_roles_from_user(self.profiled.name)

		self.assertIn("Sales User", user_roles(self.profiled.name))

	def test_update_role_applies_without_role_profile(self):
		update_user_role(self.plain.name, "Sales Manager")

		self.assertTrue({"Sales Manager", "Sales User"} <= user_roles(self.plain.name))

	def test_invitation_throws_when_existing_user_has_role_profile(self):
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(doctype="CRM Invitation", email=self.profiled.name, role="Sales Manager").insert(
				ignore_permissions=True
			)
