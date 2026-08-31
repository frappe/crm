# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase

from crm.api import sms as S


class TestSMS(IntegrationTestCase):
	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def make_lead(self, mobile_no="+391112223334"):
		return frappe.get_doc(
			{
				"doctype": "CRM Lead",
				"first_name": "SMS",
				"last_name": "Test",
				"mobile_no": mobile_no,
			}
		).insert()

	def test_incoming_sms_links_to_lead_by_number(self):
		lead = self.make_lead()
		doc = S.create_sms(
			type="Incoming",
			from_number=lead.mobile_no,
			to="+390000000000",
			message="ciao",
		)
		self.assertEqual(doc.status, "Received")
		self.assertEqual(doc.reference_doctype, "CRM Lead")
		self.assertEqual(doc.reference_name, lead.name)

	def test_get_sms_messages_returns_thread(self):
		lead = self.make_lead(mobile_no="+391112220000")
		S.create_sms(type="Incoming", from_number=lead.mobile_no, to="+390000000000", message="in")
		S.create_sms(
			type="Outgoing",
			from_number="+390000000000",
			to=lead.mobile_no,
			message="out",
			reference_doctype="CRM Lead",
			reference_name=lead.name,
			status="Sent",
		)
		thread = S.get_sms_messages("CRM Lead", lead.name)
		self.assertEqual(len(thread), 2)
		self.assertEqual([m.type for m in thread], ["Incoming", "Outgoing"])

	def test_send_sms_requires_message_and_number(self):
		lead = self.make_lead(mobile_no="+391112221111")
		with self.assertRaises(frappe.ValidationError):
			S.send_sms("CRM Lead", lead.name, to=lead.mobile_no, message="   ")
		with self.assertRaises(frappe.ValidationError):
			S.send_sms("CRM Lead", lead.name, to="", message="hello")

	def test_send_sms_without_agent_number_throws(self):
		lead = self.make_lead(mobile_no="+391112222222")
		frappe.db.delete("CRM Telephony Agent", {"name": frappe.session.user})
		with self.assertRaises(frappe.ValidationError):
			S.send_sms("CRM Lead", lead.name, to=lead.mobile_no, message="hello")

	def test_outgoing_without_twilio_enabled_marks_failed(self):
		lead = self.make_lead(mobile_no="+391112223333")
		doc = S.create_sms(
			type="Outgoing",
			from_number="+390000000000",
			to=lead.mobile_no,
			message="hi",
			reference_doctype="CRM Lead",
			reference_name=lead.name,
		)
		S.deliver_via_twilio(doc)
		doc.reload()
		self.assertEqual(doc.status, "Failed")
