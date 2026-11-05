import frappe
from frappe.desk.form.assign_to import add as assign
from frappe.tests import IntegrationTestCase

from crm.api.interactions import record
from crm.tests.test_home import AGENT, MANAGER, make_user
from crm.tests.test_interactions import at, make_communication, make_deal, make_lead, make_whatsapp_message


def alerts(**filters):
	return frappe.get_all(
		"CRM Notification",
		filters={"type": "Reply", **filters},
		fields=["to_user", "reference_doctype", "reference_name", "notification_type_doctype"],
		order_by="to_user",
	)


def assign_to(doctype, name, *users):
	assign({"assign_to": list(users), "doctype": doctype, "name": name})


class TestReplyAlerts(IntegrationTestCase):
	def setUp(self):
		make_user(AGENT, "Sales User")
		make_user(MANAGER, "Sales User", "Sales Manager")
		self.lead = make_lead()
		frappe.db.delete("CRM Notification", {"type": "Reply"})

	def tearDown(self):
		frappe.flags.in_import = False
		frappe.db.rollback()

	def test_inbound_email_alerts_every_assignee(self):
		assign_to("CRM Lead", self.lead, AGENT, MANAGER)
		email = make_communication("CRM Lead", self.lead, "Received", at(0))

		rows = alerts()
		self.assertEqual([row.to_user for row in rows], [AGENT, MANAGER])
		self.assertEqual(rows[0].reference_name, self.lead)
		self.assertEqual(rows[0].notification_type_doctype, "Communication")
		self.assertEqual(len(alerts(notification_type_doc=email.name)), 2)

	def test_owner_is_alerted_when_nobody_is_assigned(self):
		frappe.db.set_value("CRM Lead", self.lead, "lead_owner", AGENT)
		make_communication("CRM Lead", self.lead, "Received", at(0))
		self.assertEqual([row.to_user for row in alerts()], [AGENT])

	def test_sender_who_is_a_user_is_not_alerted(self):
		assign_to("CRM Lead", self.lead, AGENT, MANAGER)
		email = make_communication("CRM Lead", self.lead, "Received", at(0))
		frappe.db.delete("CRM Notification", {"type": "Reply"})
		email.db_set("sender", f"Agent <{AGENT}>")
		email.db_set("communication_date", at(5))
		email.reload().save(ignore_permissions=True)
		self.assertEqual([row.to_user for row in alerts()], [MANAGER])

	def test_outbound_email_raises_no_alert(self):
		assign_to("CRM Lead", self.lead, AGENT)
		make_communication("CRM Lead", self.lead, "Sent", at(0))
		self.assertEqual(alerts(), [])

	def test_message_older_than_the_last_one_raises_no_alert(self):
		assign_to("CRM Lead", self.lead, AGENT)
		record("CRM Lead", self.lead, "Inbound", at(10))
		make_communication("CRM Lead", self.lead, "Received", at(0))
		self.assertEqual(alerts(), [])

	def test_converted_lead_alerts_once_on_its_deal(self):
		assign_to("CRM Lead", self.lead, MANAGER)
		deal = make_deal(self.lead)
		assign_to("CRM Deal", deal, AGENT)
		frappe.db.set_value("CRM Lead", self.lead, "converted", 1)

		make_communication("CRM Lead", self.lead, "Received", at(0))

		rows = alerts()
		self.assertEqual([(row.to_user, row.reference_doctype) for row in rows], [(AGENT, "CRM Deal")])
		self.assertEqual(rows[0].reference_name, deal)

	def test_import_raises_no_alert(self):
		assign_to("CRM Lead", self.lead, AGENT)
		frappe.flags.in_import = True
		make_communication("CRM Lead", self.lead, "Received", at(0))
		self.assertEqual(alerts(), [])


class TestWhatsAppReplyAlerts(IntegrationTestCase):
	def setUp(self):
		make_user(AGENT, "Sales User")
		self.lead = make_lead()
		assign_to("CRM Lead", self.lead, AGENT)
		frappe.db.delete("CRM Notification", {"type": ("in", ("Reply", "WhatsApp"))})

	def tearDown(self):
		frappe.db.rollback()

	def test_incoming_message_alerts_once(self):
		message = make_whatsapp_message(self.lead, "Incoming", at(0))
		message.run_method("on_update")
		message.run_method("on_submit")

		rows = alerts()
		self.assertEqual(
			[(row.to_user, row.notification_type_doctype) for row in rows], [(AGENT, "WA Message")]
		)
		self.assertFalse(frappe.db.exists("CRM Notification", {"type": "WhatsApp"}))
		self.assertEqual(frappe.db.get_value("CRM Notification", {"type": "Reply"}, "message"), "Hello")

	def test_outgoing_message_and_reaction_raise_no_alert(self):
		make_whatsapp_message(self.lead, "Outgoing", at(0))
		make_whatsapp_message(self.lead, "Incoming", at(5), reaction="👍")
		self.assertEqual(alerts(), [])
