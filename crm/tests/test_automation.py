# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import json

import frappe
from frappe.tests import IntegrationTestCase

from crm.automation import engine


def make_automation(title, steps, trigger_event="Lead Created", **kw):
	payload = {
		"doctype": "CRM Automation",
		"title": title,
		"enabled": 1,
		"trigger_event": trigger_event,
		"steps": json.dumps(steps),
	}
	payload.update(kw)
	return frappe.get_doc(payload).insert()


def make_lead(**kw):
	payload = {
		"doctype": "CRM Lead",
		"first_name": "Auto",
		"last_name": "Test",
		"email": "auto@example.com",
		"mobile_no": "+390000000001",
	}
	payload.update(kw)
	return frappe.get_doc(payload).insert()


def get_enrollment(automation, lead):
	name = frappe.db.get_value(
		"CRM Automation Enrollment",
		{"automation": automation, "reference_doctype": "CRM Lead", "reference_name": lead},
	)
	return frappe.get_doc("CRM Automation Enrollment", name) if name else None


class TestAutomation(IntegrationTestCase):
	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	# ---- validation ----

	def test_invalid_step_type_rejected(self):
		with self.assertRaises(frappe.ValidationError):
			make_automation("bad-steps", [{"type": "explode"}])

	def test_wait_without_duration_rejected(self):
		with self.assertRaises(frappe.ValidationError):
			make_automation("bad-wait", [{"type": "wait"}])

	def test_stop_if_requires_condition(self):
		with self.assertRaises(frappe.ValidationError):
			make_automation("bad-stop", [{"type": "stop_if"}])

	# ---- enrollment + execution ----

	def test_lead_created_enrolls_and_completes(self):
		auto = make_automation(
			"welcome-flow",
			[
				{"type": "add_tag_comment", "comment": "Ciao {{ first_name }}"},
				{"type": "notify", "message": "Nuovo lead {{ lead_name }}"},
			],
		)
		lead = make_lead()
		enr = get_enrollment(auto.name, lead.name)
		self.assertIsNotNone(enr)
		self.assertEqual(enr.status, "Completed")
		self.assertEqual(len(enr.logs), 2)
		self.assertEqual({log.status for log in enr.logs}, {"Success"})
		# the comment was rendered against the lead
		comment = frappe.get_all(
			"Comment",
			filters={"reference_doctype": "CRM Lead", "reference_name": lead.name},
			pluck="content",
		)
		self.assertTrue(any("Auto" in c for c in comment))

	def test_wait_pauses_enrollment_and_scheduler_resumes(self):
		auto = make_automation(
			"drip-flow",
			[
				{"type": "add_tag_comment", "comment": "step 1"},
				{"type": "wait", "hours": 2},
				{"type": "add_tag_comment", "comment": "step 2"},
			],
		)
		lead = make_lead(email="drip@example.com")
		enr = get_enrollment(auto.name, lead.name)
		self.assertEqual(enr.status, "Waiting")
		self.assertEqual(enr.current_step, 1)
		self.assertIsNotNone(enr.wait_until)

		# force the wait to be due and tick the scheduler path
		enr.db_set("wait_until", frappe.utils.add_to_date(frappe.utils.now_datetime(), hours=-1))
		engine.advance_enrollment(enr.name)
		enr.reload()
		self.assertEqual(enr.status, "Completed")
		self.assertEqual(len(enr.logs), 2)

	def test_trigger_condition_filters_enrollment(self):
		auto = make_automation(
			"only-webform",
			[{"type": "add_tag_comment", "comment": "x"}],
			trigger_condition=json.dumps({"field": "email", "operator": "contains", "value": "@matchme.com"}),
		)
		lead = make_lead(email="nomatch@example.com")
		self.assertIsNone(get_enrollment(auto.name, lead.name))
		lead2 = make_lead(email="yes@matchme.com")
		self.assertIsNotNone(get_enrollment(auto.name, lead2.name))

	def test_no_reenrollment_by_default(self):
		auto = make_automation(
			"status-flow",
			[{"type": "add_tag_comment", "comment": "x"}],
			trigger_event="Lead Status Changed",
		)
		lead = make_lead()
		other_status = frappe.get_all(
			"CRM Lead Status", filters={"name": ["!=", lead.status]}, pluck="name", limit=1
		)
		self.assertTrue(other_status)
		lead.status = other_status[0]
		lead.save()
		first = get_enrollment(auto.name, lead.name)
		self.assertIsNotNone(first)
		lead.reload()
		lead.status = frappe.get_all(
			"CRM Lead Status", filters={"name": ["!=", lead.status]}, pluck="name", limit=1
		)[0]
		lead.save()
		count = frappe.db.count(
			"CRM Automation Enrollment",
			{"automation": auto.name, "reference_name": lead.name},
		)
		self.assertEqual(count, 1)

	def test_step_condition_skips(self):
		auto = make_automation(
			"conditional-step",
			[
				{
					"type": "add_tag_comment",
					"comment": "x",
					"condition": {"field": "email", "operator": "contains", "value": "@never.com"},
				}
			],
		)
		lead = make_lead()
		enr = get_enrollment(auto.name, lead.name)
		self.assertEqual(enr.status, "Completed")
		self.assertEqual(enr.logs[0].status, "Skipped")

	def test_stop_if_exits(self):
		auto = make_automation(
			"stop-flow",
			[
				{"type": "stop_if", "condition": {"field": "email", "operator": "is_set"}},
				{"type": "add_tag_comment", "comment": "never reached"},
			],
		)
		lead = make_lead()
		enr = get_enrollment(auto.name, lead.name)
		self.assertEqual(enr.status, "Exited")
		self.assertEqual(len(enr.logs), 1)

	def test_set_field_updates_reference(self):
		other_status = frappe.get_all("CRM Lead Status", pluck="name", limit=2)
		self.assertGreaterEqual(len(other_status), 2)
		auto = make_automation(
			"set-status",
			[{"type": "set_field", "field": "status", "value": other_status[1]}],
		)
		lead = make_lead(status=other_status[0])
		lead.reload()
		self.assertEqual(lead.status, other_status[1])
		enr = get_enrollment(auto.name, lead.name)
		self.assertEqual(enr.status, "Completed")

	def test_exit_on_reply(self):
		auto = make_automation(
			"reply-exit",
			[
				{"type": "add_tag_comment", "comment": "1"},
				{"type": "wait", "days": 1},
				{"type": "add_tag_comment", "comment": "2"},
			],
			exit_on_reply=1,
		)
		lead = make_lead(mobile_no="+390000000099")
		enr = get_enrollment(auto.name, lead.name)
		self.assertEqual(enr.status, "Waiting")

		sms = frappe.get_doc(
			{
				"doctype": "CRM SMS Message",
				"type": "Incoming",
				"from": "+390000000099",
				"to": "+390000000000",
				"message": "reply!",
				"status": "Received",
				"reference_doctype": "CRM Lead",
				"reference_name": lead.name,
			}
		).insert(ignore_permissions=True)
		self.assertTrue(sms)
		enr.reload()
		self.assertEqual(enr.status, "Exited")

	def test_failed_step_does_not_block_sequence(self):
		auto = make_automation(
			"resilient-flow",
			[
				{"type": "set_field", "field": "definitely_not_a_field", "value": "x"},
				{"type": "add_tag_comment", "comment": "still runs"},
			],
		)
		lead = make_lead()
		enr = get_enrollment(auto.name, lead.name)
		self.assertEqual(enr.status, "Completed")
		self.assertEqual(enr.logs[0].status, "Failed")
		self.assertEqual(enr.logs[1].status, "Success")
