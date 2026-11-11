# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

import frappe
from frappe.tests import IntegrationTestCase


class TestAutomationIcons(IntegrationTestCase):
	"""The Automation Flow page draws these icons; an entry without one gets a generic fallback."""

	def test_every_crm_event_has_an_icon(self):
		events = {}
		for entry in frappe.get_hooks("automation_events", app_name="crm"):
			events.update(entry)

		self.assertTrue(events)
		for name, schema in events.items():
			self.assertTrue(schema.get("icon", "").startswith("lucide-"), name)

	def test_every_crm_action_has_an_icon(self):
		paths = frappe.get_hooks("automation_actions", app_name="crm")

		self.assertTrue(paths)
		for path in paths:
			self.assertTrue((frappe.get_attr(path).icon or "").startswith("lucide-"), path)
