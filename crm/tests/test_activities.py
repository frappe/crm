# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import json

import frappe
from frappe.permissions import add_permission, update_permission_property
from frappe.tests import IntegrationTestCase

from crm.api.activities import _version_activities, get_activities, handle_multiple_versions

VERSION_TYPES = ("changed", "added", "removed")
RESTRICTED_FIELD = "permlevel_secret"
RESTRICTED_VALUE = "salary is 100000"


class TestActivities(IntegrationTestCase):
	def setUp(self):
		frappe.db.savepoint("test_activities")

	def tearDown(self):
		frappe.db.rollback(save_point="test_activities")

	# ------------------------------------------------------------------
	# Field changes -> activities
	# ------------------------------------------------------------------

	def test_zero_and_empty_values(self):
		fields = {f: {"label": f.title(), "options": None} for f in ("a", "b", "c", "d", "e", "f")}
		version = frappe._dict(
			creation="2026-01-01 10:00:00",
			owner="Administrator",
			data=json.dumps(
				{
					"changed": [
						["a", 10, 0],  # 10 -> 0 is a change, not a removal
						["b", None, ""],  # empty -> empty is a no-op
						["c", 0.0, None],  # numeric fields flip 0 <-> None on plain saves
						["d", 1, None],  # value -> empty is a removal
						["e", 0, 5],  # 0 is a real old value
						["f", None, 3],
					]
				}
			),
		)
		activities = {a["data"]["field"]: a for a in _version_activities([version], fields, [], False)}

		self.assertEqual(sorted(activities), ["a", "d", "e", "f"])
		self.assertEqual(activities["a"]["activity_type"], "changed")
		self.assertEqual((activities["a"]["data"]["old_value"], activities["a"]["data"]["value"]), (10, 0))
		self.assertEqual(activities["d"]["activity_type"], "removed")
		self.assertEqual(activities["e"]["activity_type"], "changed")
		self.assertEqual(activities["f"]["activity_type"], "added")

	def test_currency_set_to_zero_shows_as_change(self):
		lead = make_lead()
		lead.annual_revenue = 1000
		lead.save(ignore_version=False)
		lead.annual_revenue = 0
		lead.save(ignore_version=False)

		activity = field_change(get_activities(lead.name)[0], "annual_revenue", "changed")
		df = frappe.get_meta("CRM Lead").get_field("annual_revenue")
		# Frappe stores 1000 pre-formatted but 0 raw; the timeline formats 0 the same way
		self.assertEqual(activity["data"]["old_value"], frappe.format_value(1000, df))
		self.assertEqual(activity["data"]["value"], frappe.format_value(0, df))

	def test_zero_uses_the_deal_currency(self):
		deal = make_deal(None)
		deal.currency = "USD"
		deal.deal_value = 500
		deal.save(ignore_version=False)
		deal.deal_value = 0
		deal.save(ignore_version=False)

		activity = field_change(get_activities(deal.name)[0], "deal_value", "changed")
		zero = frappe.format_value(0, frappe.get_meta("CRM Deal").get_field("deal_value"), currency="USD")
		self.assertEqual(activity["data"]["value"], zero)
		# same currency symbol on both sides, not the site default
		self.assertEqual(activity["data"]["old_value"].split()[0], zero.split()[0])

	def test_derived_lead_name_is_not_shown(self):
		lead = make_lead()
		lead.first_name = "Renamed"
		lead.save(ignore_version=False)

		fields = {e["data"]["field"] for e in entries(get_activities(lead.name)[0])}
		self.assertIn("first_name", fields)
		self.assertNotIn("lead_name", fields)

	def test_system_set_sla_status_is_not_shown(self):
		deal = make_deal(None)
		deal.sla_status = "Failed"
		deal.next_step = "Call back"
		deal.save(ignore_version=False)

		fields = {e["data"]["field"] for e in entries(get_activities(deal.name)[0])}
		self.assertIn("next_step", fields)
		self.assertNotIn("sla_status", fields)

	def test_check_field_turned_off_is_a_change(self):
		fields = {"flag": {"label": "Flag", "options": None}}
		version = frappe._dict(
			creation="2026-01-01 10:00:00",
			owner="Administrator",
			data=json.dumps({"changed": [["flag", 1, 0]]}),
		)
		(activity,) = _version_activities([version], fields, [], False)
		self.assertEqual(activity["activity_type"], "changed")
		self.assertEqual((activity["data"]["old_value"], activity["data"]["value"]), (1, 0))

	def test_won_shows_status_with_closed_date_in_the_same_group(self):
		deal = make_deal(None)
		deal.status = "Won"
		deal.save(ignore_version=False)

		(group,) = [g for g in version_groups(get_activities(deal.name)[0]) if "status" in group_fields(g)]
		# the status change leads; the auto-set closed date sits under "+1 more"
		self.assertEqual(group["data"]["field"], "status")
		self.assertIn("closed_date", group_fields(group))

	# ------------------------------------------------------------------
	# Grouping
	# ------------------------------------------------------------------

	def test_one_save_is_one_group(self):
		lead = make_lead()
		lead.website = "example.com"
		lead.job_title = "CEO"
		lead.save(ignore_version=False)
		lead.website = "example.org"
		lead.save(ignore_version=False)

		groups = version_groups(get_activities(lead.name)[0])

		self.assertEqual([group_fields(g) for g in groups], [{"website"}, {"website", "job_title"}])
		# a single-field save is a plain entry, with no empty group attached
		self.assertNotIn("other_versions", groups[0])
		self.assertEqual(len(groups[1]["other_versions"]), 1)

	def test_non_version_activities_never_get_other_versions(self):
		lead = make_lead()
		lead.website = "example.com"
		lead.save(ignore_version=False)

		for activity in get_activities(lead.name)[0]:
			if activity["activity_type"] not in VERSION_TYPES:
				self.assertNotIn("other_versions", activity)

	def test_grouping_splits_on_save_owner_and_other_activities(self):
		def change(field, creation, owner="a@example.com"):
			return {
				"activity_type": "changed",
				"creation": creation,
				"owner": owner,
				"data": {"field": field},
			}

		grouped = handle_multiple_versions(
			[
				change("f1", "3"),
				change("f2", "3"),
				change("f3", "3", owner="b@example.com"),  # same time, other user
				{"activity_type": "comment", "creation": "3", "owner": "a@example.com"},
				change("f4", "3"),  # the comment ends the previous group
				change("f5", "2"),  # same user, different save
			]
		)

		self.assertEqual(
			[(a["activity_type"], group_fields(a)) for a in grouped],
			[
				("changed", {"f1", "f2"}),
				("changed", {"f3"}),
				("comment", set()),
				("changed", {"f4"}),
				("changed", {"f5"}),
			],
		)
		self.assertEqual(grouped[0]["data"]["field"], "f1")

	# ------------------------------------------------------------------
	# Deal timeline (merged with the lead it came from)
	# ------------------------------------------------------------------

	def test_deal_timeline_keeps_every_lead_and_deal_change(self):
		lead = make_lead()
		lead.website = "lead.example.com"
		lead.job_title = "CTO"
		lead.save(ignore_version=False)

		deal = make_deal(lead.name)
		# lead edits after conversion sit right next to the deal's own changes,
		# which is where grouping lead and deal twice used to nest or drop them
		lead.job_title = "CEO"
		lead.no_of_employees = "11-50"
		lead.save(ignore_version=False)
		lead.website = "lead2.example.com"
		lead.save(ignore_version=False)

		deal.next_step = "Send proposal"
		deal.website = "deal.example.com"
		deal.save(ignore_version=False)

		activities = get_activities(deal.name)[0]
		groups = version_groups(activities)

		lead_fields = set().union(*(group_fields(g) for g in groups if g["is_lead"]))
		deal_fields = set().union(*(group_fields(g) for g in groups if not g["is_lead"]))
		self.assertTrue({"website", "job_title", "no_of_employees"} <= lead_fields)
		self.assertTrue({"website", "next_step"} <= deal_fields)

		for group in groups:
			members = [group, *group.get("other_versions", [])]
			# grouped once only: no group inside a group
			self.assertFalse(any("other_versions" in m for m in members[1:]))
			# every member comes from the same save
			self.assertEqual(len({(m["owner"], m["creation"], m["is_lead"]) for m in members}), 1)


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

	def test_multi_field_save_one_restricted(self):
		"""A single save changing both an unrestricted and a restricted field must
		surface the unrestricted field for the rep and hide the restricted one.
		This is the exact regression caught by the changed[0]-only bug: iterating
		only the first entry in data["changed"] would drop whichever field wasn't
		first, so one of the two was always silently lost.
		"""
		lead = frappe.get_doc(
			{"doctype": "CRM Lead", "lead_owner": "rep@permlevel.test", "first_name": "Multi"}
		)
		lead.flags.ignore_mandatory = True
		lead.insert(ignore_permissions=True)

		# Change both fields in the same save so they land in the same Version record.
		lead.status = "Contacted"
		lead.set(RESTRICTED_FIELD, RESTRICTED_VALUE)
		lead.save(ignore_permissions=True, ignore_version=False)

		rep_activities = self.activities_as("rep@permlevel.test", lead.name)
		mgr_fields = changed_fields(self.activities_as("mgr@permlevel.test", lead.name))

		# Rep sees the unrestricted field...
		self.assertIn("status", changed_fields(rep_activities))
		# ...but not the restricted one (no value leak either).
		self.assertNotIn(RESTRICTED_FIELD, changed_fields(rep_activities))
		self.assertNotIn(RESTRICTED_VALUE, frappe.as_json(rep_activities))

		# Manager sees both.
		self.assertIn("status", mgr_fields)
		self.assertIn(RESTRICTED_FIELD, mgr_fields)

	def test_docinfo_is_not_sent_with_activities(self):
		"""docinfo carries the raw, unfiltered versions, so it must not reach the client."""
		lead = self.make_lead_with_restricted_change()
		response = frappe.response
		frappe.response = frappe._dict()
		try:
			self.activities_as("rep@permlevel.test", lead.name)
			self.assertNotIn("docinfo", frappe.response)
		finally:
			frappe.response = response


def make_lead():
	lead = frappe.get_doc({"doctype": "CRM Lead", "first_name": "Timeline"})
	lead.flags.ignore_mandatory = True
	return lead.insert()


def make_deal(lead_name):
	deal = frappe.get_doc({"doctype": "CRM Deal", "lead": lead_name})
	deal.flags.ignore_mandatory = True
	deal.flags.ignore_links = True
	return deal.insert()


def field_change(activities, field, activity_type):
	return next(
		e
		for e in entries(activities)
		if e["data"].get("field") == field and e["activity_type"] == activity_type
	)


def version_groups(activities):
	return [a for a in activities if a["activity_type"] in VERSION_TYPES]


def entries(activities):
	"""Every field-change entry, including those inside groups."""
	for group in version_groups(activities):
		yield group
		yield from group.get("other_versions", [])


def group_fields(activity):
	data = activity.get("data")
	fields = {data["field"]} if isinstance(data, dict) and data.get("field") else set()
	return fields | {o["data"]["field"] for o in activity.get("other_versions", [])}


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
