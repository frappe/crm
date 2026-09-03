# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

"""WhatsApp onboarding: signed state, account routing, webhook fan-out.

These cover the hub machinery only — the messaging itself belongs to
frappe_whatsapp, which may not be installed on the test bench.
"""

import base64
import hashlib
import hmac
import json
import time

import frappe
from frappe.tests import IntegrationTestCase

from crm.integrations.whatsapp import coexistence as C
from crm.integrations.whatsapp import signup as S
from crm.integrations.whatsapp import webhook as W


def make_state(site, issued_at=None):
	payload = json.dumps({"t": issued_at or int(time.time()), "site": site})
	return f"{base64.urlsafe_b64encode(payload.encode()).decode()}.{S.sign_state(payload)}"


class TestWhatsAppSignup(IntegrationTestCase):
	def setUp(self):
		frappe.local.conf["meta_relay_secret"] = "shared-whatsapp-secret"

	def tearDown(self):
		frappe.local.conf.pop("meta_relay_secret", None)
		frappe.local.conf.pop("meta_relay_sites", None)
		frappe.db.rollback()

	def test_state_roundtrip(self):
		parsed = S.parse_state(make_state("https://cliente.it"))
		self.assertEqual(parsed["site"], "https://cliente.it")

	def test_state_with_forged_site_is_rejected(self):
		good = json.dumps({"t": int(time.time()), "site": "https://cliente.it"})
		forged = json.dumps({"t": int(time.time()), "site": "https://ladro.it"})
		bad = f"{base64.urlsafe_b64encode(forged.encode()).decode()}.{S.sign_state(good)}"
		self.assertIsNone(S.parse_state(bad))
		self.assertIsNone(S.parse_state("rubbish"))
		self.assertIsNone(S.parse_state(None))

	def test_expired_state_is_rejected(self):
		self.assertIsNone(S.parse_state(make_state("https://cliente.it", issued_at=1)))

	def test_allowed_site_respects_the_closed_list(self):
		self.assertTrue(S.allowed_site("https://qualunque.it"))
		frappe.local.conf["meta_relay_sites"] = ["https://buono.it"]
		self.assertTrue(S.allowed_site("https://buono.it/"))
		self.assertFalse(S.allowed_site("https://ignoto.it"))

	def test_claim_route_registers_and_is_idempotent(self):
		S.claim_route("WABA1", "PHONE1", "+39 333 1234567", "https://cliente.it")
		row = frappe.db.get_value(
			"Meta WhatsApp Route", "WABA1", ["site_url", "phone_number_id"], as_dict=True
		)
		self.assertEqual(row.site_url, "https://cliente.it")
		self.assertEqual(row.phone_number_id, "PHONE1")
		S.claim_route("WABA1", "PHONE2", "+39 333 1234567", "https://cliente.it")
		self.assertEqual(frappe.db.get_value("Meta WhatsApp Route", "WABA1", "phone_number_id"), "PHONE2")

	def test_claim_route_refuses_takeover(self):
		S.claim_route("WABA2", "PHONE3", "", "https://primo.it")
		with self.assertRaises(frappe.ValidationError):
			S.claim_route("WABA2", "PHONE3", "", "https://ladro.it")
		self.assertEqual(frappe.db.get_value("Meta WhatsApp Route", "WABA2", "site_url"), "https://primo.it")


class TestWhatsAppWebhookRouting(IntegrationTestCase):
	def tearDown(self):
		frappe.db.rollback()

	def test_route_by_waba_id(self):
		S.claim_route("WABA10", "PHONE10", "", "https://cliente.it/")
		self.assertEqual(W.route_for({"id": "WABA10", "changes": []}), "https://cliente.it")

	def test_route_falls_back_to_phone_number_id(self):
		S.claim_route("WABA11", "PHONE11", "", "https://altro.it")
		entry = {
			"id": "SCONOSCIUTA",
			"changes": [{"value": {"metadata": {"phone_number_id": "PHONE11"}}}],
		}
		self.assertEqual(W.route_for(entry), "https://altro.it")

	def test_unknown_account_is_not_routed(self):
		self.assertIsNone(W.route_for({"id": "MAI_VISTA", "changes": []}))

	def test_webhook_signature(self):
		settings = frappe.get_doc("CRM Meta Settings")
		settings.app_secret = "app-secret"
		settings.save()
		frappe.clear_document_cache("CRM Meta Settings", "CRM Meta Settings")

		body = b'{"object":"whatsapp_business_account","entry":[]}'
		good = "sha256=" + hmac.new(b"app-secret", body, hashlib.sha256).hexdigest()
		self.assertTrue(W.valid_signature(good, body))
		self.assertFalse(W.valid_signature("sha256=deadbeef", body))
		self.assertFalse(W.valid_signature(None, body))


class TestCoexistenceRouting(IntegrationTestCase):
	"""The Coexistence fields must not be sent to frappe_whatsapp, which only
	understands `messages`."""

	def test_split_entry_separates_the_two_worlds(self):
		entry = {
			"id": "WABA20",
			"changes": [
				{"field": "messages", "value": {"a": 1}},
				{"field": "smb_message_echoes", "value": {"b": 2}},
				{"field": "history", "value": {"c": 3}},
			],
		}
		parts = dict(W.split_entry(entry))
		self.assertEqual([c["field"] for c in parts["messages"]["changes"]], ["messages"])
		self.assertEqual(
			[c["field"] for c in parts["coexistence"]["changes"]],
			["smb_message_echoes", "history"],
		)

	def test_split_entry_with_only_messages_has_no_coexistence_part(self):
		entry = {"id": "WABA21", "changes": [{"field": "messages", "value": {}}]}
		self.assertEqual([kind for kind, _ in W.split_entry(entry)], ["messages"])

	def test_message_body_reads_the_common_types(self):
		self.assertEqual(C.message_body({"type": "text", "text": {"body": "ciao"}}), ("ciao", "text"))
		self.assertEqual(
			C.message_body({"type": "reaction", "reaction": {"emoji": "👍"}}), ("👍", "reaction")
		)
		self.assertEqual(C.message_body({"type": "image", "image": {"caption": "foto"}}), ("foto", "image"))
		self.assertEqual(C.message_body({"type": "image", "image": {}}), ("[image]", "image"))

	def test_business_number_is_normalised(self):
		self.assertEqual(
			C.business_number({"metadata": {"display_phone_number": "+393331234567"}}),
			"393331234567",
		)
		self.assertEqual(C.business_number({}), "")
