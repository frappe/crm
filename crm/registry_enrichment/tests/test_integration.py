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

from crm.registry_enrichment import api, client, config, install, permissions, tasks
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


def _make_scoped_user(email, allowed_org=None):
	"""A Sales Manager user, optionally restricted to a single CRM Organization.

	A User Permission is the mechanism by which a manager loses access to a record: with
	one in place the user reads only ``allowed_org`` (and records linked to it), so it
	models "created a Run, then lost access to its referenced record".
	"""
	if not frappe.db.exists("User", email):
		user = frappe.new_doc("User")
		user.email = email
		user.first_name = "Scoped"
		user.send_welcome_email = 0
		user.append("roles", {"role": "Sales Manager"})
		user.insert(ignore_permissions=True)
	if allowed_org and not frappe.db.exists(
		"User Permission",
		{"user": email, "allow": "CRM Organization", "for_value": allowed_org},
	):
		frappe.get_doc(
			{
				"doctype": "User Permission",
				"user": email,
				"allow": "CRM Organization",
				"for_value": allowed_org,
			}
		).insert(ignore_permissions=True)
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

	def test_multiple_stale_inflight_runs_failed_in_single_update(self):
		# Several stale in-flight Runs for the same record must all be failed in ONE database
		# statement (no write per Run inside the loop), with no live Run adopted.
		org = _new_org()
		first = tasks.write_run("CRM Organization", org.name, "12345678000195", "Queued")
		second = tasks.write_run("CRM Organization", org.name, "12345678000195", "Running")
		stale = frappe.utils.add_to_date(
			frappe.utils.now_datetime(), minutes=-(tasks.INFLIGHT_TIMEOUT_MINUTES + 1)
		)
		for name in (first, second):
			frappe.db.set_value("CRM Registry Enrichment Run", name, "modified", stale, update_modified=False)

		# Spy on the query builder entry point to prove exactly one update statement is issued
		# for both stale Runs, rather than one per Run.
		real_update = tasks.frappe.qb.update
		update_calls = []

		def counting_update(*args, **kwargs):
			update_calls.append(args)
			return real_update(*args, **kwargs)

		with mock.patch.object(tasks.frappe.qb, "update", side_effect=counting_update):
			result = tasks.find_inflight_run("CRM Organization", org.name)

		# No Run is within the freshness window, so none is adopted as live.
		self.assertIsNone(result)
		# One bulk update covered both stale Runs.
		self.assertEqual(len(update_calls), 1)
		for name in (first, second):
			row = frappe.db.get_value(
				"CRM Registry Enrichment Run",
				name,
				["status", "error", "finished_at"],
				as_dict=True,
			)
			self.assertEqual(row.status, "Failed")
			self.assertEqual(row.error, "Timed out waiting for the background worker.")
			self.assertTrue(row.finished_at)


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


class RunPermissionScopeTest(IntegrationTestCase):
	"""Finding 1: a Run must never widen visibility beyond its referenced record."""

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def _run_for_org(self):
		org = _new_org()
		return frappe.get_doc(
			"CRM Registry Enrichment Run",
			tasks.write_run("CRM Organization", org.name, "12345678000195", "Queued"),
		)

	def test_sales_user_role_removed_from_run(self):
		# Sales User was dropped from the doctype permissions entirely, so a user without a
		# management role cannot read any Run regardless of the referenced record.
		run = self._run_for_org()
		self.assertFalse(
			frappe.has_permission("CRM Registry Enrichment Run", "read", run.name, user=_make_minimal_user())
		)

	def test_system_manager_reads_run(self):
		run = self._run_for_org()
		self.assertTrue(frappe.has_permission("CRM Registry Enrichment Run", "read", run.name))

	def test_has_permission_scopes_to_referenced_record(self):
		# The controller hook allows a read only when the caller can read the referenced doc.
		run = self._run_for_org()
		user = _make_minimal_user()
		with mock.patch.object(permissions.frappe, "has_permission", return_value=False):
			self.assertFalse(permissions.has_permission(run, "read", user=user))
		with mock.patch.object(permissions.frappe, "has_permission", return_value=True):
			self.assertTrue(permissions.has_permission(run, "read", user=user))

	def test_has_permission_defers_for_non_read_ptype(self):
		# Controllers may only deny; write/delete are left to the role permissions.
		run = self._run_for_org()
		self.assertTrue(permissions.has_permission(run, "write", user=_make_minimal_user()))

	def test_query_conditions_scope_by_reference_not_owner(self):
		# System Manager reads everything; the condition scopes by the referenced record,
		# never by ownership.
		self.assertEqual(permissions.get_permission_query_conditions("Administrator"), "")

		org = _new_org()
		scoped = _make_scoped_user("re-cond@example.com", allowed_org=org.name)
		condition = permissions.get_permission_query_conditions(scoped)
		self.assertNotIn("owner", condition)
		self.assertIn("reference_doctype", condition)
		# The query builder renders the subquery with uppercase keywords and backtick-quoted
		# identifiers; this asserts the same meaning (reference_name matched against a
		# subquery over the referenced table) in the builder's form.
		self.assertIn("`reference_name` IN (SELECT `name` FROM", condition)

	def test_query_conditions_deny_all_without_readable_reference(self):
		# A user who cannot read any referenced doctype sees no Run at all.
		self.assertEqual(permissions.get_permission_query_conditions(_make_minimal_user()), "1=0")


class RunQueryScopeTest(IntegrationTestCase):
	"""Finding 1 (list/report/export): the list query binds each Run to current access on
	its referenced record, run through real users with ``frappe.get_list``."""

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def _run_owned_by(self, org_name, owner):
		run = tasks.write_run("CRM Organization", org_name, "12345678000195", "Queued")
		frappe.db.set_value("CRM Registry Enrichment Run", run, "owner", owner, update_modified=False)
		return run

	def _listed_names(self):
		return {row.name for row in frappe.get_list("CRM Registry Enrichment Run", limit_page_length=0)}

	def test_owner_without_current_access_cannot_list_run(self):
		# The scoped user OWNS both runs but keeps access only to `allowed`; the run for the
		# record they can no longer read must not appear, even though they created it.
		allowed = _new_org()
		denied = _new_org()
		email = _make_scoped_user("re-scoped@example.com", allowed_org=allowed.name)
		run_allowed = self._run_owned_by(allowed.name, email)
		run_denied = self._run_owned_by(denied.name, email)

		frappe.set_user(email)
		names = self._listed_names()
		self.assertIn(run_allowed, names)
		self.assertNotIn(run_denied, names)

	def test_system_manager_lists_run_regardless_of_owner(self):
		org = _new_org()
		run = self._run_owned_by(org.name, _make_minimal_user())
		# Administrator (System Manager) is not scoped and sees the run.
		self.assertIn(run, self._listed_names())

	def test_single_quote_reference_name_is_escaped(self):
		# The organization name (its primary key, and the value build_match_conditions
		# inlines) carries a single quote: the query must run without error and still return
		# the run, proving the value is escaped rather than breaking or injecting.
		org = _new_org(organization_name="O'Reilly Registry " + frappe.generate_hash(length=4))
		email = _make_scoped_user("re-quote@example.com", allowed_org=org.name)
		run = self._run_owned_by(org.name, email)

		frappe.set_user(email)
		self.assertIn(run, self._listed_names())


class QueueRunRowLockTest(IntegrationTestCase):
	"""Finding 2: run creation is serialized by a row lock on the target record so
	concurrent requests cannot strand a run, without any manual commit."""

	def setUp(self):
		_ensure_settings()

	def tearDown(self):
		frappe.db.rollback()

	def test_locks_target_row_before_lookup(self):
		# The target record's row is locked (SELECT ... FOR UPDATE) before find_inflight_run,
		# so the find-then-create window is serialized inside the request transaction.
		org = _new_org()
		events = []
		real_get_value = api.frappe.db.get_value
		real_find = tasks.find_inflight_run

		def spy_get_value(doctype, filters=None, *args, **kwargs):
			if doctype == "CRM Organization" and filters == org.name and kwargs.get("for_update"):
				events.append("lock")
			return real_get_value(doctype, filters, *args, **kwargs)

		def spy_find(*args, **kwargs):
			events.append("find")
			return real_find(*args, **kwargs)

		with mock.patch.object(api.frappe.db, "get_value", side_effect=spy_get_value):
			with mock.patch.object(tasks, "find_inflight_run", side_effect=spy_find):
				with mock.patch.object(tasks.frappe, "enqueue"):
					api.enrich("CRM Organization", org.name)

		self.assertIn("lock", events)
		self.assertIn("find", events)
		self.assertLess(events.index("lock"), events.index("find"))

	def test_second_request_reuses_run_under_lock(self):
		# Once a Queued run exists, a following request reuses it under the row lock instead
		# of inserting a second row for the deduplicated job.
		org = _new_org()
		with mock.patch.object(tasks.frappe, "enqueue") as enq:
			first = api.enrich("CRM Organization", org.name)
			second = api.enrich("CRM Organization", org.name)
		self.assertEqual(first["run"], second["run"])
		enq.assert_called_once()


class ApiArgumentValidationTest(IntegrationTestCase):
	"""Finding 3: caller-supplied arguments must be non-empty strings before any use."""

	def tearDown(self):
		frappe.db.rollback()

	def test_require_str_rejects_non_string(self):
		for bad in (123, None, 0, [], {}):
			with self.assertRaises(frappe.ValidationError):
				api._require_str(bad, "X")

	def test_require_str_rejects_empty(self):
		for bad in ("", "   "):
			with self.assertRaises(frappe.ValidationError):
				api._require_str(bad, "X")

	def test_require_str_returns_valid_value(self):
		self.assertEqual(api._require_str("ok", "X"), "ok")

	def test_enrich_rejects_blank_reference(self):
		_ensure_settings()
		with self.assertRaises(frappe.ValidationError):
			api.enrich("", "CRM-1")
		with self.assertRaises(frappe.ValidationError):
			api.enrich("CRM Organization", "   ")

	def test_retry_rejects_blank_run(self):
		with self.assertRaises(frappe.ValidationError):
			api.retry("   ")


class TimeoutBoundsTest(IntegrationTestCase):
	"""Finding 4: request_timeout is bounded on save and clamped defensively downstream."""

	def tearDown(self):
		frappe.db.rollback()

	def test_settings_rejects_out_of_band(self):
		for bad in (-1, 61, 3600):
			settings = frappe.get_doc("CRM Registry Enrichment Settings")
			settings.request_timeout = bad
			with self.assertRaises(frappe.ValidationError):
				settings.save(ignore_permissions=True)

	def test_settings_accepts_in_band(self):
		for ok in (0, 1, 15, 60):
			settings = frappe.get_doc("CRM Registry Enrichment Settings")
			settings.request_timeout = ok
			settings.save(ignore_permissions=True)

	def test_config_get_timeout_clamps(self):
		class _Fake:
			def __init__(self, value):
				self._value = value

			def get(self, _key):
				return self._value

		cases = ((3600, 60), (-5, 1), (30, 30), (0, config.DEFAULT_TIMEOUT))
		for stored, expected in cases:
			with mock.patch.object(config, "get_settings", return_value=_Fake(stored)):
				self.assertEqual(config.get_timeout(), expected)

	def test_client_fetch_clamps_timeout(self):
		for given, expected in ((3600, 60), (-5, 1), (30, 30), (0, client.DEFAULT_TIMEOUT)):
			with mock.patch.object(client, "_session") as session:
				session.return_value.get.side_effect = RuntimeError("stop")
				with self.assertRaises(client.RegistryLookupError):
					client.fetch("12345678000195", 6, "token", timeout=given)
				self.assertEqual(session.return_value.get.call_args.kwargs["timeout"], expected)


class RunPermissionBranchTest(IntegrationTestCase):
	"""Finding 1: cover the allow branches of the controller hook."""

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def test_system_manager_bypasses_reference_scope(self):
		org = _new_org()
		run = frappe.get_doc(
			"CRM Registry Enrichment Run",
			tasks.write_run("CRM Organization", org.name, "12345678000195", "Queued"),
		)
		# A System Manager is allowed without touching the referenced record.
		with mock.patch.object(permissions.frappe, "has_permission") as ref:
			self.assertTrue(permissions.has_permission(run, "read", user="Administrator"))
		ref.assert_not_called()

	def test_allows_when_run_has_no_reference(self):
		orphan = frappe._dict(reference_doctype=None, reference_name=None)
		self.assertTrue(permissions.has_permission(orphan, "read", user=_make_minimal_user()))


class RetryReenqueueTest(IntegrationTestCase):
	"""Finding 2/3: retry re-runs a stored run through the atomic queue path."""

	def setUp(self):
		_ensure_settings()

	def tearDown(self):
		frappe.db.rollback()

	def test_retry_reenqueues_from_run(self):
		org = _new_org()
		source = tasks.write_run("CRM Organization", org.name, "12345678000195", "Failed")
		with mock.patch.object(tasks.frappe, "enqueue") as enq:
			result = api.retry(source)
		self.assertTrue(result["queued"])
		enq.assert_called_once()
