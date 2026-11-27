import inspect
import types
import typing

import frappe
from frappe.desk.form.assign_to import add as assign_add
from frappe.tests import IntegrationTestCase

from crm.api import doc, record
from crm.fcrm.doctype.crm_deal.test_crm_deal import create_test_deal

REPLACED = {
	"get_assigned_users": "get_assignees",
	"remove_assignments": "remove_assignees",
	"add_seen": "mark_as_seen",
	"get_linked_docs_of_document": "get_linked_records",
	"remove_linked_doc_reference": "unlink_records",
	"delete_bulk_docs": "delete_records",
}


class AgentApiRules:
	"""Every whitelisted method in `api_module` follows the agent-first API rules.

	Reads are GET only, writes POST only; `reads_with_post` are reads whose
	arguments do not fit a query string, so they take POST too.
	"""

	api_module = None
	methods = frozenset()
	reads = frozenset()
	reads_with_post = frozenset()

	def test_module_has_exactly_its_methods(self):
		self.assertEqual({fn.__name__ for fn in whitelisted_functions(self.api_module)}, set(self.methods))

	def test_first_docstring_line_is_short_and_every_argument_has_a_line(self):
		for fn in whitelisted_functions(self.api_module):
			docstring = inspect.getdoc(fn)
			self.assertTrue(docstring, fn.__name__)
			self.assertLess(len(docstring.splitlines()[0]), 80, fn.__name__)
			lines = docstring.splitlines()
			for name in inspect.signature(fn).parameters:
				self.assertTrue(any(line.startswith(f"{name}: ") for line in lines), f"{fn.__name__}({name})")

	def test_arguments_have_real_types_not_json_text(self):
		for fn in whitelisted_functions(self.api_module):
			for name, parameter in inspect.signature(fn).parameters.items():
				self.assertIsNot(parameter.annotation, inspect.Parameter.empty, f"{fn.__name__}({name})")
				self.assertFalse(is_json_text(parameter.annotation), f"{fn.__name__}({name})")

	def test_reads_are_get_only_and_writes_are_post_only(self):
		for fn in whitelisted_functions(self.api_module):
			methods = frappe.allowed_http_methods_for_whitelisted_func[fn]
			if fn.__name__ in self.reads_with_post:
				expected = ("GET", "POST", "QUERY")
			elif fn.__name__ in self.reads:
				expected = ("GET", "QUERY")
			else:
				expected = ("POST",)
			self.assertEqual(methods, expected, fn.__name__)


class TestRecordApiRules(AgentApiRules, IntegrationTestCase):
	api_module = record
	methods = frozenset({*REPLACED.values(), "get_activities", "update_record"})
	reads = frozenset({"get_assignees", "get_linked_records", "get_activities"})

	def test_reads_do_not_write(self):
		deal = create_test_deal(organization="Record API Read Org")
		assign_add({"assign_to": ["crm.user1@example.com"], "doctype": "CRM Deal", "name": deal.name})

		writes = frappe.db.transaction_writes
		self.assertIn("crm.user1@example.com", record.get_assignees("CRM Deal", deal.name))
		linked = record.get_linked_records("CRM Organization", deal.organization)
		self.assertIn(deal.name, [d["reference_docname"] for d in linked])
		self.assertEqual(frappe.db.transaction_writes, writes)


class TestDeprecatedDocMethods(IntegrationTestCase):
	"""The old crm.api.doc paths stay whitelisted and point to their replacements."""

	def test_old_paths_name_their_replacement(self):
		for old, new in REPLACED.items():
			fn = getattr(doc, old)
			replacement = f"crm.api.record.{new}"
			self.assertIn(fn, frappe.whitelisted, old)
			self.assertEqual(fn.replaced_by, replacement)
			self.assertEqual(inspect.getdoc(fn), f"Deprecated: use {replacement}.")
			self.assertIn(frappe.get_attr(replacement), frappe.whitelisted)

	def test_old_paths_still_accept_json_text(self):
		deal = create_test_deal(organization="Record API Old Path Org")
		assign_add({"assign_to": ["crm.user1@example.com"], "doctype": "CRM Deal", "name": deal.name})

		doc.remove_assignments("CRM Deal", deal.name, '["crm.user1@example.com"]')
		self.assertEqual(
			doc.get_assigned_users("CRM Deal", deal.name, "fallback@example.com"), ["fallback@example.com"]
		)

		task = frappe.get_doc(
			doctype="CRM Task",
			title="Old path task",
			reference_doctype="CRM Deal",
			reference_docname=deal.name,
		).insert()
		linked = doc.get_linked_docs_of_document("CRM Deal", deal.name)
		self.assertIn(task.name, [d["reference_docname"] for d in linked])
		items = frappe.as_json([{"doctype": "CRM Task", "docname": task.name}])
		self.assertEqual(doc.remove_linked_doc_reference(items), "success")
		self.assertFalse(frappe.db.get_value("CRM Task", task.name, "reference_docname"))

		doc.add_seen("CRM Deal", deal.name)
		self.assertIn("Administrator", frappe.parse_json(frappe.db.get_value("CRM Deal", deal.name, "_seen")))

		self.assertEqual(doc.delete_bulk_docs("CRM Deal", frappe.as_json([deal.name])), "success")
		self.assertFalse(frappe.db.exists("CRM Deal", deal.name))


class TestUnlinkRecords(IntegrationTestCase):
	def test_returns_only_the_records_it_unlinked(self):
		deal = create_test_deal(organization="Record API Unlink Org")
		task = frappe.get_doc(
			doctype="CRM Task",
			title="Unlink task",
			reference_doctype="CRM Deal",
			reference_docname=deal.name,
		).insert()

		unlinked = record.unlink_records(
			[
				{"doctype": "CRM Task", "docname": task.name},
				{"doctype": "CRM Task", "docname": "missing-task"},
			]
		)

		self.assertEqual(unlinked, [{"doctype": "CRM Task", "docname": task.name}])


def whitelisted_functions(module):
	return [
		fn
		for _, fn in inspect.getmembers(module, inspect.isfunction)
		if fn in frappe.whitelisted and fn.__module__ == module.__name__
	]


def is_json_text(annotation):
	"""A `str` that may also hold a list or dict is JSON text, like `str | list`."""
	if typing.get_origin(annotation) not in (typing.Union, types.UnionType):
		return False
	members = typing.get_args(annotation)
	return str in members and any((typing.get_origin(m) or m) in (list, dict) for m in members)
