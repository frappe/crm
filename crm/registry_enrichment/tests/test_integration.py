# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""IntegrationTestCase tests for the Frappe layer (real test DB).

Covers the API guards (feature disabled / no token / invalid CNPJ / permission),
the enqueue options (per-doc job_id + deduplicate), and the worker end to end with
``client.fetch`` mocked so nothing leaves the box: a completed run fills the mapped
fields and creates a linked Address, Fill-if-empty never clobbers user data, and a
registry error records a Failed run.
"""

from __future__ import annotations

from unittest import mock

import frappe
from frappe.tests import IntegrationTestCase

from crm.registry_enrichment import api, client, install, tasks
from crm.registry_enrichment.tests.fixtures import cnpj_package6

VALID_CNPJ = "12.345.678/0001-95"
TEST_TOKEN = "5ae973d7a997af13f0aaf2bf60e65803"


def _ensure_settings(enabled=1, token=TEST_TOKEN):
	"""Put the Settings Single into a known state (mappings seeded, feature toggled)."""
	settings = frappe.get_doc("CRM Registry Enrichment Settings")
	if not settings.field_mappings:
		# Migrate normally seeds these; add them here without the custom-field DDL
		# (an ALTER would auto-commit and break the test transaction).
		for source_key, target_doctype, target_fieldname, write_policy, create_link in install.FIELD_MAPPINGS:
			settings.append(
				"field_mappings",
				{
					"enabled": 1,
					"source_key": source_key,
					"target_doctype": target_doctype,
					"target_fieldname": target_fieldname,
					"write_policy": write_policy,
					"create_missing_link": create_link,
				},
			)
	settings.enabled = enabled
	settings.api_token = token
	settings.save(ignore_permissions=True)


def _new_org(**kwargs):
	doc = frappe.new_doc("CRM Organization")
	doc.organization_name = kwargs.pop("organization_name", "Registry Org " + frappe.generate_hash(length=4))
	doc.tax_id = kwargs.pop("tax_id", VALID_CNPJ)
	for key, value in kwargs.items():
		doc.set(key, value)
	doc.insert(ignore_permissions=True)
	return doc


def _make_minimal_user():
	"""A user with no CRM Organization role, for permission tests."""
	email = "re-noperm@example.com"
	if not frappe.db.exists("User", email):
		user = frappe.new_doc("User")
		user.email = email
		user.first_name = "No"
		user.last_name = "Perm"
		user.send_welcome_email = 0
		user.insert(ignore_permissions=True)
	return email


class ApiGuardTest(IntegrationTestCase):
	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def test_throws_when_feature_disabled(self):
		_ensure_settings(enabled=0)
		org = _new_org()
		with self.assertRaises(frappe.ValidationError):
			api.enrich("CRM Organization", org.name)

	def test_throws_when_token_missing(self):
		_ensure_settings(enabled=1, token="")
		org = _new_org()
		with self.assertRaises(frappe.ValidationError):
			api.enrich("CRM Organization", org.name)

	def test_throws_on_disallowed_doctype(self):
		_ensure_settings()
		with self.assertRaises(frappe.ValidationError):
			api.enrich("ToDo", "anything")

	def test_throws_on_invalid_tax_id(self):
		_ensure_settings()
		org = _new_org(tax_id="123")
		with self.assertRaises(frappe.ValidationError):
			api.enrich("CRM Organization", org.name)

	def test_requires_write_permission(self):
		_ensure_settings()
		org = _new_org()
		frappe.set_user(_make_minimal_user())
		with self.assertRaises((frappe.PermissionError, frappe.ValidationError)):
			api.enrich("CRM Organization", org.name)

	def test_enrich_routes_are_rate_limited(self):
		for fn in (api.enrich, api.retry):
			self.assertTrue(hasattr(fn, "__wrapped__"), fn.__name__)


class EnqueueOptionsTest(IntegrationTestCase):
	def tearDown(self):
		frappe.db.rollback()

	def test_job_is_deduplicated_per_doc(self):
		with mock.patch.object(tasks, "get_timeout", return_value=15):
			with mock.patch.object(tasks.frappe, "enqueue") as enq:
				tasks.enqueue_enrichment("CRM Organization", "ORG-XYZ")
		enq.assert_called_once()
		kwargs = enq.call_args.kwargs
		self.assertEqual(kwargs["job_id"], "registry-enrich-CRM Organization-ORG-XYZ")
		self.assertTrue(kwargs["deduplicate"])
		self.assertTrue(kwargs["enqueue_after_commit"])
		self.assertEqual(kwargs["queue"], "long")


class AutoEnrichOnCreateTest(IntegrationTestCase):
	def tearDown(self):
		frappe.db.rollback()

	def _settings(self, **overrides):
		s = {"enabled": 1, "auto_enrich": 1}
		s.update(overrides)
		return frappe._dict(s)

	def test_skips_without_valid_cnpj(self):
		from crm.registry_enrichment import config

		with mock.patch.object(config, "get_settings", return_value=self._settings()):
			with mock.patch.object(tasks.frappe, "enqueue") as enq:
				tasks.auto_enrich_on_create(frappe._dict(doctype="CRM Organization", name="O1", tax_id="123"))
		enq.assert_not_called()

	def test_enqueues_for_valid_cnpj(self):
		from crm.registry_enrichment import config

		with mock.patch.object(config, "get_settings", return_value=self._settings()):
			with mock.patch.object(tasks.frappe, "enqueue") as enq:
				tasks.auto_enrich_on_create(
					frappe._dict(doctype="CRM Organization", name="O2", tax_id=VALID_CNPJ)
				)
		enq.assert_called_once()
		self.assertEqual(enq.call_args.kwargs["job_id"], "registry-enrich-CRM Organization-O2")


class RunEnrichmentTest(IntegrationTestCase):
	def setUp(self):
		_ensure_settings()
		self.payload = cnpj_package6()

	def tearDown(self):
		frappe.db.rollback()

	def test_completed_run_fills_fields_and_links_address(self):
		org = _new_org(trade_name="", industry="")
		with mock.patch.object(client, "fetch", return_value=self.payload):
			tasks.run_enrichment("CRM Organization", org.name, user="Administrator")

		org.reload()
		# tax_id is seeded "Always refresh": the org was created with a formatted CNPJ,
		# and after the run the stored value is the canonical normalized document.
		self.assertEqual(org.tax_id, "12345678000195")
		self.assertEqual(org.trade_name, "Token Test")
		self.assertEqual(org.industry, "Technology")
		self.assertTrue(org.address)

		address = frappe.get_doc("Address", org.address)
		self.assertEqual(address.city, "Montes Claros")
		self.assertEqual(address.pincode, "39400000")

		run = frappe.get_last_doc("CRM Registry Enrichment Run", filters={"reference_name": org.name})
		self.assertEqual(run.status, "Completed")
		self.assertGreater(run.fields_updated, 0)
		self.assertIn("TOKEN TEST", run.raw_json)

	def test_run_history_drops_account_metadata(self):
		org = _new_org()
		with mock.patch.object(client, "fetch", return_value=self.payload):
			tasks.run_enrichment("CRM Organization", org.name, user="Administrator")
		run = frappe.get_last_doc("CRM Registry Enrichment Run", filters={"reference_name": org.name})
		# Account/response metadata is stripped from the persisted payload.
		self.assertNotIn("saldo", run.raw_json)
		self.assertNotIn("consultaID", run.raw_json)
		self.assertNotIn("delay", run.raw_json)
		# Company registry data is retained.
		self.assertIn("razao", run.raw_json)

	def test_fill_if_empty_does_not_overwrite_user_data(self):
		org = _new_org(trade_name="Hand-written by sales")
		with mock.patch.object(client, "fetch", return_value=self.payload):
			tasks.run_enrichment("CRM Organization", org.name, user="Administrator")
		org.reload()
		self.assertEqual(org.trade_name, "Hand-written by sales")

	def test_registry_error_records_failed_run(self):
		org = _new_org()
		error = client.RegistryLookupError(200, "Invalid CNPJ (check digits do not match).")
		with mock.patch.object(client, "fetch", side_effect=error):
			tasks.run_enrichment("CRM Organization", org.name, user="Administrator")

		run = frappe.get_last_doc("CRM Registry Enrichment Run", filters={"reference_name": org.name})
		self.assertEqual(run.status, "Failed")
		self.assertIn("Invalid CNPJ", run.error)


class QueueRunReuseTest(IntegrationTestCase):
	def setUp(self):
		_ensure_settings()

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def test_enrich_twice_reuses_single_queued_run(self):
		# A manual click racing an auto-fire (or a double click) must not strand a second
		# Queued Run: the second enqueue would be dropped by the shared job_id dedupe.
		org = _new_org()
		with mock.patch.object(tasks.frappe, "enqueue") as enq:
			first = api.enrich("CRM Organization", org.name)
			second = api.enrich("CRM Organization", org.name)

		self.assertEqual(first["run"], second["run"])
		enq.assert_called_once()
		queued = frappe.get_all(
			"CRM Registry Enrichment Run",
			filters={"reference_name": org.name, "status": "Queued"},
		)
		self.assertEqual(len(queued), 1)

	def test_stale_inflight_run_is_failed_and_replaced(self):
		# A Queued Run whose worker never ran must not block new attempts forever.
		org = _new_org()
		with mock.patch.object(tasks.frappe, "enqueue"):
			first = api.enrich("CRM Organization", org.name)
		stale = frappe.utils.add_to_date(
			frappe.utils.now_datetime(), minutes=-(tasks.INFLIGHT_TIMEOUT_MINUTES + 1)
		)
		frappe.db.set_value(
			"CRM Registry Enrichment Run", first["run"], "modified", stale, update_modified=False
		)
		with mock.patch.object(tasks.frappe, "enqueue") as enq:
			second = api.enrich("CRM Organization", org.name)

		self.assertNotEqual(first["run"], second["run"])
		enq.assert_called_once()
		self.assertEqual(frappe.db.get_value("CRM Registry Enrichment Run", first["run"], "status"), "Failed")
		self.assertEqual(
			frappe.db.get_value("CRM Registry Enrichment Run", second["run"], "status"), "Queued"
		)


class LinkMasterCaseTest(IntegrationTestCase):
	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def test_reuses_existing_industry_master_ignoring_case(self):
		from crm.registry_enrichment import mapper

		# A name no default seed uses, so the stored casing is fully under test control.
		master = "Registry Case Probe"
		if not frappe.db.exists("CRM Industry", master):
			frappe.get_doc({"doctype": "CRM Industry", "industry": master}).insert(ignore_permissions=True)
		# The incoming label differs only in case from the stored master. The canonical
		# master name must be returned, never a case-divergent duplicate value.
		value = mapper._ensure_link_target("CRM Organization", "industry", master.lower())
		self.assertEqual(value, master)
		self.assertEqual(
			frappe.db.count("CRM Industry", {"name": ("like", "registry case probe")}),
			1,
		)


class SeedDefaultsIdempotencyTest(IntegrationTestCase):
	def tearDown(self):
		frappe.db.rollback()

	def test_seed_defaults_is_idempotent(self):
		# The Custom Field DDL is mocked out: an ALTER auto-commits and would break the
		# test transaction. This exercises the mapping-seeding idempotency and confirms
		# the idempotent custom-field creator is invoked on every run.
		settings = frappe.get_doc("CRM Registry Enrichment Settings")
		settings.set("field_mappings", [])
		settings.save(ignore_permissions=True)

		with mock.patch.object(install, "create_custom_fields") as ccf:
			install.seed_defaults()
			install.seed_defaults()

		# Custom-field creation invoked once per seed, always with the full set.
		self.assertEqual(ccf.call_count, 2)
		ccf.assert_called_with(install.CUSTOM_FIELDS, ignore_validate=True)
		self.assertEqual(sum(len(fields) for fields in install.CUSTOM_FIELDS.values()), 15)

		# Running the seeder twice must not duplicate mapping rows.
		settings.reload()
		self.assertEqual(len(settings.field_mappings), len(install.FIELD_MAPPINGS))
