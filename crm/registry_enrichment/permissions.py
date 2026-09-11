# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Row-level access control for ``CRM Registry Enrichment Run``.

A Run stores the raw registry payload and error text for one CRM Lead or Organization,
so it must never widen visibility beyond the referenced record. The doctype grants read
only to System Manager and Sales Manager; these hooks add defense in depth so a manager
who cannot see the referenced Lead/Organization cannot read its Run either.

``has_permission`` gates single-document access (form view, the ``retry`` endpoint's
``read`` check): a read is allowed only when the user can read the referenced record.
``get_permission_query_conditions`` gates the list/report/export view, which never invokes
the controller hook per row. System Manager keeps full visibility; every other reader is
scoped to the records they can currently read, by matching each Run against a subquery on
its referenced doctype that carries that user's live permission scope. Ownership is not
used: a manager who created a Run and later lost access to the referenced record stops
seeing the Run, because the subquery reflects current access rather than who created it.
"""

from __future__ import annotations

import frappe
import frappe.desk.reportview
from frappe.query_builder import Criterion
from pypika.terms import LiteralValue

from crm.registry_enrichment.config import ENRICHABLE_DOCTYPES

# ptypes that expose the run's stored registry data. Everything else (write, delete,
# create) is left to the role permissions, which already restrict it to System Manager.
_READ_PTYPES = frozenset({"read", "email", "print", "export", "report", "share"})


def has_permission(doc, ptype=None, user=None, **kwargs):
	"""Deny read of a Run whose referenced record the user cannot read.

	Controller permission hooks may only deny, never grant, so this returns ``True``
	(defer to role permissions) in every case except an unauthorized read.
	"""
	if ptype not in _READ_PTYPES:
		return True

	user = user or frappe.session.user
	if "System Manager" in frappe.get_roles(user):
		return True

	reference_doctype = doc.get("reference_doctype")
	reference_name = doc.get("reference_name")
	if not reference_doctype or not reference_name:
		# No linked record to scope against; the role permission already gates the Run.
		return True

	return frappe.has_permission(reference_doctype, "read", reference_name, user=user)


def get_permission_query_conditions(user=None, **kwargs):
	"""List/report/export scope: bind every Run to current access on its referenced record.

	System Manager (and Administrator) read everything. For any other reader, a Run is
	visible only when its referenced record is one the user can currently read: for each
	enrichable doctype the user can read, the Run is matched against a subquery over that
	doctype carrying the user's live permission scope (the same match conditions the
	doctype's own list query applies). This scopes by current access, not by who created
	the Run, so revoking access to the referenced record also hides its Run. When the user
	can read none of the referenced doctypes, every row is denied.

	The condition is assembled with ``frappe.qb`` (the repo's query builder) and rendered
	once, so the builder does the quoting; no value is concatenated into SQL by hand.
	"""
	user = user or frappe.session.user
	if user == "Administrator" or "System Manager" in frappe.get_roles(user):
		return ""

	Run = frappe.qb.DocType("CRM Registry Enrichment Run")
	clauses = []
	for doctype in ENRICHABLE_DOCTYPES:
		if not frappe.has_permission(doctype, "read", user=user):
			# The user cannot read this doctype at all, so no Run referencing it is visible.
			continue

		DT = frappe.qb.DocType(doctype)
		subquery = frappe.qb.from_(DT).select(DT.name)

		# The user's current permission scope on the referenced doctype: an SQL fragment
		# built by the framework from the user's User Permissions, never from user input.
		# An empty string means unrestricted read, so no filter is added and the subquery
		# selects every record; otherwise it is applied as a builder term.
		match = frappe.desk.reportview.build_match_conditions(doctype, user=user, as_condition=True)
		if match:
			subquery = subquery.where(LiteralValue(match))

		clauses.append((Run.reference_doctype == doctype) & Run.reference_name.isin(subquery))

	if not clauses:
		# No referenced doctype is readable: deny every row (never fall back to ownership).
		condition = LiteralValue("1=0")
	else:
		condition = Criterion.any(clauses)

	return condition.get_sql(with_namespace=True, quote_char="`", secondary_quote_char="'")
