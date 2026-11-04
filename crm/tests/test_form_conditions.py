# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

from typing import ClassVar

import frappe
from frappe.tests import IntegrationTestCase

from crm.api import form as F
from crm.utils.form_conditions import field_required, field_visible, form_value_errors, truthy


class TestFormConditions(IntegrationTestCase):
	"""The server reads a form field's conditions the way the public page does
	(frontend/tests/unit/webFormConditionalEval.test.js runs the same cases there)."""

	doc: ClassVar[dict] = {"organization": "Acme", "first_name": "Al", "n": "10", "items": [1]}

	def test_same_answers_as_the_page(self):
		doc = self.doc
		self.assertTrue(truthy("organization", doc, False))
		self.assertFalse(truthy("missing", doc, False))
		self.assertTrue(truthy('eval:doc.organization == "Acme"', doc, False))
		self.assertFalse(truthy('eval:doc.organization == "Other"', doc, False))
		self.assertTrue(truthy("eval:doc.n > 5", doc, False))
		self.assertTrue(truthy("eval:doc.first_name && doc.organization", doc, False))
		self.assertTrue(truthy("eval:!doc.missing", doc, False))
		self.assertTrue(truthy("eval:(doc.a || doc.organization) && doc.first_name", doc, False))
		self.assertTrue(truthy("", doc, True))
		self.assertFalse(truthy("   ", doc, False))
		self.assertTrue(truthy("items", doc, False))

	def test_loose_comparisons_like_javascript(self):
		doc = {"size": "10", "empty": "", "flag": 1, "zero": "0"}
		self.assertTrue(truthy("eval:doc.size == 10", doc, False))
		self.assertTrue(truthy("eval:doc.size === '10'", doc, False))
		self.assertTrue(truthy("eval:doc.flag == true", doc, False))
		self.assertTrue(truthy("eval:doc.missing == null", doc, False))
		self.assertTrue(truthy("eval:doc.size != 'x' && doc.size >= 10", doc, False))
		# a non-empty string is truthy, even "0"
		self.assertTrue(truthy("zero", doc, False))
		self.assertFalse(truthy("empty", doc, False))

	def test_anything_else_falls_back_and_never_runs(self):
		for expr in (
			"eval:window",
			"eval:globalThis",
			'eval:fetch("/x")',
			'eval:doc.constructor.constructor("return 1")()',
			'eval:(0).constructor.constructor("return 1")()',
			"eval:doc.x = 1",
			"eval:__import__('os')",
			"eval:doc.x if 1 else 2",
			"fn:anything",
		):
			self.assertFalse(truthy(expr, self.doc, False), expr)
			self.assertTrue(truthy(expr, self.doc, True), expr)

	def test_required_only_while_shown_and_editable(self):
		f = frappe._dict(
			fieldname="website",
			reqd=0,
			depends_on="eval:doc.organization",
			mandatory_depends_on="organization",
		)
		self.assertTrue(field_required(f, {"organization": "Acme"}))
		self.assertFalse(field_visible(f, {}))
		self.assertFalse(field_required(f, {}))
		f.read_only_depends_on = "organization"
		self.assertFalse(field_required(f, {"organization": "Acme"}))

	def test_missing_answers_are_named(self):
		fields = [
			frappe._dict(fieldname="organization", fieldtype="Data", label="Company"),
			frappe._dict(
				fieldname="website",
				fieldtype="Data",
				label="Website",
				mandatory_depends_on='eval:doc.organization == "Acme"',
			),
		]
		self.assertIsNone(form_value_errors(fields, {"organization": "Other"}))
		self.assertEqual(form_value_errors(fields, {"organization": "Acme"}), "Please fill in: Website")
		self.assertIsNone(form_value_errors(fields, {"organization": "Acme", "website": "acme.com"}))


class TestWebFormSubmissionRules(IntegrationTestCase):
	"""A CRM web form's own required fields hold for a submission that skips the page."""

	def tearDown(self):
		frappe.flags.in_web_form = False
		frappe.form_dict.pop("web_form", None)
		frappe.db.rollback()

	def submit(self, form, **values):
		frappe.flags.in_web_form = True
		frappe.form_dict["web_form"] = form
		return frappe.get_doc({"doctype": "CRM Lead", "email": "rules@test.invalid", **values}).insert(
			ignore_permissions=True
		)

	def test_form_required_and_required_if_fields_are_enforced(self):
		form = F.save_form(
			name=None,
			form={
				"title": "Rules",
				"route": "rules-form",
				"document_type": "CRM Lead",
				"fields": [
					{"fieldname": "first_name", "fieldtype": "Data", "reqd": 1},
					{"fieldname": "email", "fieldtype": "Data", "reqd": 1},
					# required on the form, though the Lead itself doesn't require it
					{"fieldname": "organization", "fieldtype": "Data", "reqd": 1},
					{
						"fieldname": "website",
						"fieldtype": "Data",
						"mandatory_depends_on": 'eval:doc.organization == "Acme"',
					},
				],
			},
		)["name"]
		with self.assertRaises(frappe.ValidationError):
			self.submit(form, first_name="Ada")
		with self.assertRaises(frappe.ValidationError):
			self.submit(form, first_name="Ada", organization="Acme")
		self.assertTrue(self.submit(form, first_name="Ada", organization="Acme", website="acme.com").name)
		self.assertTrue(self.submit(form, first_name="Bo", organization="Other").name)
