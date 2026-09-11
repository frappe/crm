# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Row-level access control for ``CRM Registry Enrichment Run``.

A Run stores the raw registry payload and error text for one CRM Lead or Organization,
so it must never widen visibility beyond the referenced record. The doctype grants read
only to System Manager and Sales Manager; these hooks add defense in depth so a manager
who cannot see the referenced Lead/Organization cannot read its Run either.

``has_permission`` gates single-document access (form view, the ``retry`` endpoint's
``read`` check): a read is allowed only when the user can read the referenced record.
``get_permission_query_conditions`` gates the list/report view, which never invokes the
controller hook per row. System Manager keeps full visibility; every other reader is
scoped to the runs they own, the documented simple-and-correct choice over a generic
cross-doctype subquery (the exact per-record gate is enforced by ``has_permission``).
"""

from __future__ import annotations

import frappe

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
	"""List/report scope: full visibility for System Manager, owned runs otherwise."""
	user = user or frappe.session.user
	if "System Manager" in frappe.get_roles(user):
		return ""

	return f"`tabCRM Registry Enrichment Run`.owner = {frappe.db.escape(user)}"
