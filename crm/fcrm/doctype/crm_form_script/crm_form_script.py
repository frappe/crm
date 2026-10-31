# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

from crm.fcrm.form_script_analysis import Analysis, analyse
from crm.fcrm.form_script_analysis.patterns import UNKNOWN

NO_COUNTERPART = "No counterpart"
REWRITE = "Rewrite"
REWRITE_WITH_GAPS = "Rewrite: has calls with no counterpart"
UNKNOWN_SHAPE = "Unknown shape"


class CRMFormScript(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from crm.fcrm.doctype.crm_form_script_call.crm_form_script_call import CRMFormScriptCall

		dt: DF.Link
		enabled: DF.Check
		is_standard: DF.Check
		migration_status: DF.Literal["", "Rewrite", "Rewrite: has calls with no counterpart", "Unknown shape"]
		script: DF.Code | None
		v1_calls: DF.Table[CRMFormScriptCall]
		v1_shape: DF.Literal["", "Class-based", "setupForm", "setupList", "Unknown"]
		view: DF.Literal["Form", "List"]
	# end: auto-generated types

	def validate(self):
		in_user_env = not (
			frappe.flags.in_install
			or frappe.flags.in_patch
			or frappe.flags.in_test
			or frappe.flags.in_fixtures
		)
		if in_user_env and not self.is_new() and self.is_standard and not frappe.conf.developer_mode:
			# only enabled can be changed for standard form scripts
			if self.has_value_changed("enabled"):
				enabled_value = self.enabled
				self.reload()
				self.enabled = enabled_value
			else:
				frappe.throw(_("You need to be in developer mode to edit a Standard Form Script"))
		self.set_analysis()

	def set_analysis(self):
		analysis = analyse(self.script, self.dt, self.view)
		self.v1_shape = analysis.shape
		self.migration_status = migration_status(analysis)
		self.set(
			"v1_calls",
			[
				{
					"line": hit.line,
					"v1_call": hit.call,
					"verb": hit.verb or NO_COUNTERPART,
					"catalog_key": hit.key,
					"gap": hit.gap,
				}
				for hit in analysis.hits
			],
		)


def migration_status(analysis: Analysis) -> str:
	if analysis.shape == UNKNOWN:
		return UNKNOWN_SHAPE
	if any(hit.verb is None for hit in analysis.hits):
		return REWRITE_WITH_GAPS
	return REWRITE


def refresh_analysis(name: str):
	"""Rewrites a row's analysis without saving it, for the writers that set its script directly."""
	doc = frappe.get_doc("CRM Form Script", name)
	doc.set_analysis()
	doc.db_update()
	doc.update_child_table("v1_calls")


def get_form_script(dt, view="Form"):
	"""Returns the form script for the given doctype"""
	FormScript = frappe.qb.DocType("CRM Form Script")
	query = (
		frappe.qb.from_(FormScript)
		.select("script")
		.where(FormScript.dt == dt)
		.where(FormScript.view == view)
		.where(FormScript.enabled == 1)
	)

	doc = query.run(as_dict=True)
	if doc:
		return [d.script for d in doc] if len(doc) > 1 else doc[0].script
	else:
		return None
