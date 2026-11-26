# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import sha256_hash
from frappe.utils.password import update_password

from crm.www.crm import get_context, redirect_to_set_password

STRONG_PASSWORD = "Qx7#mLp2vT9!"


def make_user(email, roles=None):
	"""A user created the way Frappe Cloud and scripts create one: no password."""
	user = frappe.get_doc(
		doctype="User",
		user_type="System User",
		email=email,
		first_name=email.split("@")[0].title(),
		send_welcome_email=0,
	).insert(ignore_permissions=True)

	if roles:
		user.append_roles(*roles)
		user.save(ignore_permissions=True)

	return user


class TestPasswordSetup(IntegrationTestCase):
	def setUp(self):
		self.user = make_user("no-password@example.com", roles=["System Manager"])
		frappe.db.set_single_value("FCRM Settings", "setup_completed", 1)
		frappe.set_user(self.user.name)

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.local.flags.redirect_location = None
		frappe.local.flags.commit = False
		frappe.local.system_settings = None
		frappe.db.rollback()

	def make_sso_user(self):
		frappe.set_user("Administrator")
		self.user.append("social_logins", {"provider": "google", "userid": "1234567890"})
		self.user.save(ignore_permissions=True)
		frappe.set_user(self.user.name)

	# ---- redirect ----

	def test_redirects_to_set_password_page_with_a_working_key(self):
		with self.assertRaises(frappe.Redirect) as raised:
			redirect_to_set_password()

		# a 301 would be cached by the browser and outlive the key it points at
		self.assertEqual(raised.exception.http_status_code, 302)

		# the reset key is written on a GET, which is rolled back otherwise
		self.assertTrue(frappe.local.flags.commit)

		link = frappe.local.flags.redirect_location
		self.assertIn("/update-password?key=", link)

		key = link.split("key=")[1]
		self.assertEqual(frappe.db.get_value("User", self.user.name, "reset_password_key"), sha256_hash(key))

	def test_no_redirect_for_user_who_has_a_password(self):
		update_password(user=self.user.name, pwd=STRONG_PASSWORD)

		redirect_to_set_password()

		self.assertIsNone(frappe.local.flags.redirect_location)

	def test_no_redirect_for_sso_user(self):
		self.make_sso_user()

		redirect_to_set_password()

		self.assertIsNone(frappe.local.flags.redirect_location)

	def test_crm_page_load_redirects_a_user_without_a_password(self):
		"""The redirect is wired into the page the user actually opens."""
		with self.assertRaises(frappe.Redirect):
			get_context()

		self.assertIn("/update-password?key=", frappe.local.flags.redirect_location)

	# ---- guided setup ----

	def test_no_redirect_while_guided_setup_is_pending(self):
		"""The guided setup asks for the password in its first step."""
		frappe.db.set_single_value("FCRM Settings", "setup_completed", 0)

		redirect_to_set_password()

		self.assertIsNone(frappe.local.flags.redirect_location)

	def test_redirects_non_admin_while_guided_setup_is_pending(self):
		frappe.db.set_single_value("FCRM Settings", "setup_completed", 0)
		frappe.set_user("Administrator")
		self.user.remove_roles("System Manager")
		self.user.append_roles("Sales User")
		frappe.set_user(self.user.name)

		with self.assertRaises(frappe.Redirect):
			redirect_to_set_password()

	def test_demo_user_cannot_change_password(self):
		from frappe.core.doctype.user.test_user import test_user

		from crm.api.live_demo import validate_reset_password, validate_user

		with (
			test_user(roles=["Sales User"], generated_id=True) as user,
			patch.dict(frappe.conf, {"demo_username": user.email}),
		):
			frappe.set_user(user.name)

			with self.assertRaises(frappe.PermissionError):
				validate_user(frappe._dict(new_password=STRONG_PASSWORD), "before_validate")
			with self.assertRaises(frappe.PermissionError):
				validate_reset_password(None, "validate_reset_password")

			frappe.set_user(self.user.name)
