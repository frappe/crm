# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe
from frappe.permissions import add_permission, update_permission_property
from frappe.tests import IntegrationTestCase

from crm.api.activities import get_activities

RESTRICTED_FIELD = "permlevel_secret"
RESTRICTED_VALUE = "salary is 100000"


class TestActivityPermlevel(IntegrationTestCase):
	"""A permlevel-restricted field is hidden on the form layout, so its values
	must not leak through the activity timeline either (frappe/crm#805).

	  rep@permlevel.test  -- Sales User, owns the lead, no permlevel 1 access
	  mgr@permlevel.test  -- Sales Manager, reads permlevel 1
	"""

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		make_user("rep@permlevel.test", roles=["Sales User"])
		make_user("mgr@permlevel.test", roles=["Sales Manager"])

		if not frappe.db.exists("Custom Field", {"dt": "CRM Lead", "fieldname": RESTRICTED_FIELD}):
			frappe.get_doc(
				{
					"doctype": "Custom Field",
					"dt": "CRM Lead",
					"fieldname": RESTRICTED_FIELD,
					"label": "Permlevel Secret",
					"fieldtype": "Data",
					"permlevel": 1,
				}
			).insert(ignore_permissions=True)

		# only Sales Manager gets permlevel 1 on CRM Lead
		add_permission("CRM Lead", "Sales Manager", 1)
		update_permission_property("CRM Lead", "Sales Manager", 1, "write", 1)
		frappe.clear_cache(doctype="CRM Lead")

	def setUp(self):
		frappe.db.savepoint("test_activity_permlevel")

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback(save_point="test_activity_permlevel")

	def make_lead_with_restricted_change(self):
		lead = frappe.get_doc(
			{"doctype": "CRM Lead", "lead_owner": "rep@permlevel.test", "first_name": "Permlevel"}
		)
		lead.flags.ignore_mandatory = True
		lead.insert(ignore_permissions=True)

		lead.set(RESTRICTED_FIELD, RESTRICTED_VALUE)
		# the timeline is built from versions, which tests skip unless asked for
		lead.save(ignore_permissions=True, ignore_version=False)
		return lead

	def activities_as(self, user, name):
		frappe.set_user(user)
		try:
			activities, *_ = get_activities(name)
		finally:
			frappe.set_user("Administrator")
		return activities

	def test_restricted_field_change_is_hidden_from_activity(self):
		lead = self.make_lead_with_restricted_change()
		activities = self.activities_as("rep@permlevel.test", lead.name)

		self.assertNotIn(RESTRICTED_FIELD, changed_fields(activities))
		self.assertNotIn(RESTRICTED_VALUE, frappe.as_json(activities))

	def test_permitted_user_still_sees_the_change(self):
		lead = self.make_lead_with_restricted_change()
		activities = self.activities_as("mgr@permlevel.test", lead.name)

		self.assertIn(RESTRICTED_FIELD, changed_fields(activities))

	def test_unrestricted_fields_are_untouched(self):
		lead = self.make_lead_with_restricted_change()
		lead.status = "Qualified"
		lead.save(ignore_permissions=True, ignore_version=False)

		activities = self.activities_as("rep@permlevel.test", lead.name)
		self.assertIn("status", changed_fields(activities))
		self.assertNotIn(RESTRICTED_FIELD, changed_fields(activities))


def changed_fields(activities):
	"""Fieldnames reported by the timeline, including grouped versions."""
	fields = set()
	for activity in activities:
		for entry in [activity, *(activity.get("other_versions") or [])]:
			data = entry.get("data")
			if isinstance(data, dict) and data.get("field"):
				fields.add(data["field"])
	return fields


def make_user(email, roles=None):
	if frappe.db.exists("User", email):
		return frappe.get_doc("User", email)
	user = frappe.get_doc(
		{
			"doctype": "User",
			"email": email,
			"first_name": email.split("@")[0],
			"send_welcome_email": 0,
		}
	).insert(ignore_permissions=True)
	for role in roles or []:
		user.add_roles(role)
	return user
