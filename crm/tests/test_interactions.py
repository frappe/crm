import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_to_date, get_datetime

from crm.api.interactions import record
from crm.patches.v1_0.backfill_interaction_timestamps import execute as backfill

T0 = get_datetime("2026-01-01 10:00:00")


def at(minutes: int):
	return add_to_date(T0, minutes=minutes)


class TestInteractions(IntegrationTestCase):
	def setUp(self):
		self.lead = make_lead()

	def state(self, doctype="CRM Lead", name=None):
		return frappe.db.get_value(
			doctype,
			name or self.lead,
			["last_inbound_at", "last_outbound_at", "awaiting_reply_since"],
			as_dict=True,
		)

	def test_inbound_sets_awaiting(self):
		record("CRM Lead", self.lead, "Inbound", at(0))
		self.assertEqual(self.state().last_inbound_at, at(0))
		self.assertEqual(self.state().awaiting_reply_since, at(0))

	def test_outbound_clears_awaiting(self):
		record("CRM Lead", self.lead, "Inbound", at(0))
		record("CRM Lead", self.lead, "Outbound", at(5))
		self.assertEqual(self.state().last_outbound_at, at(5))
		self.assertIsNone(self.state().awaiting_reply_since)

	def test_newer_inbound_after_outbound_sets_awaiting_again(self):
		record("CRM Lead", self.lead, "Outbound", at(5))
		record("CRM Lead", self.lead, "Inbound", at(10))
		self.assertEqual(self.state().awaiting_reply_since, at(10))

	def test_older_timestamp_is_ignored(self):
		record("CRM Lead", self.lead, "Inbound", at(10))
		record("CRM Lead", self.lead, "Inbound", at(0))
		record("CRM Lead", self.lead, "Outbound", at(5))
		state = self.state()
		self.assertEqual(state.last_inbound_at, at(10))
		self.assertEqual(state.awaiting_reply_since, at(10))

	def test_does_not_touch_modified(self):
		modified = frappe.db.get_value("CRM Lead", self.lead, "modified")
		record("CRM Lead", self.lead, "Inbound", at(0))
		self.assertEqual(frappe.db.get_value("CRM Lead", self.lead, "modified"), modified)

	def test_converted_lead_forwards_to_latest_deal(self):
		make_deal(self.lead)
		deal = make_deal(self.lead)
		frappe.db.set_value("CRM Lead", self.lead, "converted", 1)

		record("CRM Lead", self.lead, "Inbound", at(0))

		self.assertEqual(self.state().awaiting_reply_since, at(0))
		self.assertEqual(self.state("CRM Deal", deal).awaiting_reply_since, at(0))

	def test_unconverted_lead_does_not_forward(self):
		deal = make_deal(self.lead)
		record("CRM Lead", self.lead, "Inbound", at(0))
		self.assertIsNone(self.state("CRM Deal", deal).last_inbound_at)

	def test_other_doctypes_and_missing_records_are_ignored(self):
		record("ToDo", "anything", "Inbound", at(0))
		record("CRM Lead", "missing-lead", "Inbound", at(0))
		self.assertFalse(frappe.db.exists("CRM Lead", "missing-lead"))


class TestEmailInteractions(IntegrationTestCase):
	def setUp(self):
		self.lead = make_lead()

	def state(self):
		return frappe.db.get_value(
			"CRM Lead",
			self.lead,
			["last_inbound_at", "last_outbound_at", "awaiting_reply_since"],
			as_dict=True,
		)

	def test_received_email_sets_awaiting(self):
		make_communication("CRM Lead", self.lead, "Received", at(0))
		self.assertEqual(self.state().awaiting_reply_since, at(0))

	def test_sent_email_clears_awaiting(self):
		make_communication("CRM Lead", self.lead, "Received", at(0))
		make_communication("CRM Lead", self.lead, "Sent", at(5))
		self.assertEqual(self.state().last_outbound_at, at(5))
		self.assertIsNone(self.state().awaiting_reply_since)

	def test_automated_message_is_ignored(self):
		make_communication("CRM Lead", self.lead, "Received", at(0))
		make_communication("CRM Lead", self.lead, "Sent", at(5), "Automated Message")
		state = self.state()
		self.assertIsNone(state.last_outbound_at)
		self.assertEqual(state.awaiting_reply_since, at(0))

	def test_non_crm_reference_is_ignored(self):
		todo = frappe.get_doc({"doctype": "ToDo", "description": "interactions"}).insert()
		make_communication("ToDo", todo.name, "Received", at(0))
		self.assertIsNone(self.state().last_inbound_at)


class TestBackfillInteractions(IntegrationTestCase):
	def test_backfill_from_email_history(self):
		replied = make_lead()
		make_communication("CRM Lead", replied, "Received", at(0))
		make_communication("CRM Lead", replied, "Sent", at(5))

		converted = make_lead()
		deal = make_deal(converted)
		frappe.db.set_value("CRM Lead", converted, "converted", 1)
		make_communication("CRM Lead", converted, "Received", at(10))
		make_communication("CRM Lead", converted, "Sent", at(20), "Automated Message")

		reset_interactions()
		backfill()

		self.assertIsNone(frappe.db.get_value("CRM Lead", replied, "awaiting_reply_since"))
		self.assertEqual(frappe.db.get_value("CRM Lead", replied, "last_outbound_at"), at(5))
		self.assertEqual(frappe.db.get_value("CRM Lead", converted, "awaiting_reply_since"), at(10))
		self.assertEqual(frappe.db.get_value("CRM Deal", deal, "awaiting_reply_since"), at(10))
		self.assertIsNone(frappe.db.get_value("CRM Deal", deal, "last_outbound_at"))


def make_lead() -> str:
	return frappe.get_doc({"doctype": "CRM Lead", "first_name": "Interactions"}).insert().name


def make_deal(lead: str) -> str:
	deal = frappe.get_doc({"doctype": "CRM Deal", "lead": lead})
	deal.flags.ignore_mandatory = True
	return deal.insert().name


def make_communication(doctype, name, sent_or_received, date, communication_type="Communication"):
	return frappe.get_doc(
		{
			"doctype": "Communication",
			"communication_type": communication_type,
			"communication_medium": "Email",
			"sent_or_received": sent_or_received,
			"communication_date": date,
			"subject": "Interactions",
			"content": "Hello",
			"sender": "customer@example.com",
			"reference_doctype": doctype,
			"reference_name": name,
		}
	).insert(ignore_permissions=True)


def reset_interactions():
	for doctype in ("CRM Lead", "CRM Deal"):
		frappe.db.set_value(
			doctype,
			{"name": ["is", "set"]},
			{"last_inbound_at": None, "last_outbound_at": None, "awaiting_reply_since": None},
			update_modified=False,
		)
