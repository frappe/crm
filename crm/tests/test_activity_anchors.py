# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase

from crm.api.activities import get_activities
from crm.tests import load_crm_user_test_records
from crm.tests.test_search_sqlite import SALES_USER, add_comment, add_email, add_note, make_deal, make_lead


class TestActivityAnchors(IntegrationTestCase):
	"""Search hits link to `#<name>`, so timeline rows must carry their source document's name."""

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		load_crm_user_test_records()
		cls.lead = make_lead(SALES_USER)
		cls.deal = make_deal(SALES_USER, lead=cls.lead)
		cls.comment = add_comment("CRM Lead", cls.lead, "Asked for annual pricing")
		cls.note = add_note("CRM Lead", cls.lead, "Pricing sheet sent")
		cls.email = add_email("CRM Lead", cls.lead, "<p>Can you share the enterprise tier?</p>")
		cls.automated = add_email(
			"CRM Lead", cls.lead, "Your quote is ready", communication_type="Automated Message"
		)

	def setUp(self):
		frappe.set_user(SALES_USER)
		self.addCleanup(frappe.set_user, "Administrator")

	def test_lead_timeline_rows_carry_their_source_names(self):
		self.assert_anchors(get_activities(self.lead))

	def test_deal_timeline_rows_from_its_source_lead_carry_their_source_names(self):
		self.assert_anchors(get_activities(self.deal))

	def assert_anchors(self, timeline):
		activities, _calls, notes, _tasks, _attachments = timeline
		names = {(a["activity_type"], a.get("name")) for a in activities}

		self.assertIn(("comment", self.comment), names)
		self.assertIn(("communication", self.email), names)
		self.assertIn(("communication", self.automated), names)
		self.assertIn(self.note, [n["name"] for n in notes])
