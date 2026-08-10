# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""CRM relationship graph exposed to the automation engine.

The engine never learns how a CRM record links to another one — it only asks this provider
for a relationship by name and gets `{doctype, name}` references back, which it then
allow-lists and permission-checks itself.
"""

import frappe
from frappe.automation_engine.relationships import AutomationRelationshipProvider

COMMUNICATION_REFERENCE_DOCTYPES = ["CRM Lead", "CRM Deal"]


class CRMRelationshipProvider(AutomationRelationshipProvider):
	def get_definitions(self, source_doctype: str) -> list[dict]:
		return [_public(definition) for definition in DEFINITIONS.get(source_doctype, [])]

	def resolve(self, source_doc, relationship: str, params: dict) -> list[dict]:
		definition = _definition(source_doc.doctype, relationship)
		return definition["resolve"](source_doc)

	def query(self, source_doc, relationship: str, filters: list, limit: int) -> list[dict]:
		definition = _definition(source_doc.doctype, relationship)
		linked = definition.get("linked")
		if not linked:
			return super().query(source_doc, relationship, filters, limit)
		doctype, link_filters = linked(source_doc)
		names = frappe.get_list(doctype, filters=[*link_filters, *filters], pluck="name", limit=limit)
		return [{"doctype": doctype, "name": name} for name in names]


def _definition(source_doctype: str, relationship: str) -> dict:
	for definition in DEFINITIONS.get(source_doctype, []):
		if definition["name"] == relationship:
			return definition
	frappe.throw(frappe._("Unknown CRM relationship: {0}").format(relationship))


def _public(definition) -> dict:
	return {key: value for key, value in definition.items() if key not in ("resolve", "linked")}


def _references(doctype, names) -> list[dict]:
	return [{"doctype": doctype, "name": name} for name in names if name]


def _linked(doctype, filters):
	"""Definition helper for relationships backed by a single filtered query."""
	return lambda doc: (doctype, filters(doc))


def _from_query(doctype, filters):
	return lambda doc: _references(doctype, frappe.get_all(doctype, filters=filters(doc), pluck="name"))


def _communication_filters(doc):
	return [["reference_doctype", "=", doc.doctype], ["reference_name", "=", doc.name]]


def _task_filters(doc):
	return [["reference_doctype", "=", doc.doctype], ["reference_docname", "=", doc.name]]


def _communication_reference(doc) -> list[dict]:
	if doc.reference_doctype not in COMMUNICATION_REFERENCE_DOCTYPES:
		return []
	return _references(doc.reference_doctype, [doc.reference_name])


def _lead_organization(lead) -> list[dict]:
	"""Leads hold an organization name, not a link — match it to a CRM Organization."""
	name = lead.organization and frappe.db.exists(
		"CRM Organization", {"organization_name": lead.organization}
	)
	return _references("CRM Organization", [name])


def _lead_contacts(lead) -> list[dict]:
	"""Contacts explicitly linked to the Lead, plus the one sharing its email address."""
	names = frappe.get_all(
		"Dynamic Link",
		filters={"parenttype": "Contact", "link_doctype": "CRM Lead", "link_name": lead.name},
		pluck="parent",
	)
	if lead.email:
		names += frappe.get_all("Contact Email", filters={"email_id": lead.email}, pluck="parent")
	return _references("Contact", sorted(set(names)))


def _deal_contacts(deal) -> list[dict]:
	return _references("Contact", [row.contact for row in deal.contacts or []])


DEFINITIONS: dict[str, list[dict]] = {
	"Communication": [
		{
			"name": "reference",
			"label": "Linked Lead or Deal",
			"cardinality": "one",
			"target_doctypes": COMMUNICATION_REFERENCE_DOCTYPES,
			"resolve": _communication_reference,
		}
	],
	"CRM Lead": [
		{
			"name": "organization",
			"label": "Organization",
			"cardinality": "one",
			"target_doctype": "CRM Organization",
			"resolve": _lead_organization,
		},
		{
			"name": "contacts",
			"label": "Contacts",
			"cardinality": "many",
			"target_doctype": "Contact",
			"resolve": _lead_contacts,
		},
		{
			"name": "deals",
			"label": "Deals",
			"cardinality": "many",
			"target_doctype": "CRM Deal",
			"resolve": _from_query("CRM Deal", lambda doc: {"lead": doc.name}),
			"linked": _linked("CRM Deal", lambda doc: [["lead", "=", doc.name]]),
		},
		{
			"name": "communications",
			"label": "Communications",
			"cardinality": "many",
			"target_doctype": "Communication",
			"resolve": _from_query("Communication", _communication_filters),
			"linked": _linked("Communication", _communication_filters),
		},
		{
			"name": "tasks",
			"label": "Tasks",
			"cardinality": "many",
			"target_doctype": "CRM Task",
			"resolve": _from_query("CRM Task", _task_filters),
			"linked": _linked("CRM Task", _task_filters),
		},
	],
	"CRM Deal": [
		{
			"name": "lead",
			"label": "Lead",
			"cardinality": "one",
			"target_doctype": "CRM Lead",
			"resolve": lambda doc: _references("CRM Lead", [doc.lead]),
		},
		{
			"name": "organization",
			"label": "Organization",
			"cardinality": "one",
			"target_doctype": "CRM Organization",
			"resolve": lambda doc: _references("CRM Organization", [doc.organization]),
		},
		{
			"name": "contacts",
			"label": "Contacts",
			"cardinality": "many",
			"target_doctype": "Contact",
			"resolve": _deal_contacts,
		},
		{
			"name": "communications",
			"label": "Communications",
			"cardinality": "many",
			"target_doctype": "Communication",
			"resolve": _from_query("Communication", _communication_filters),
			"linked": _linked("Communication", _communication_filters),
		},
		{
			"name": "tasks",
			"label": "Tasks",
			"cardinality": "many",
			"target_doctype": "CRM Task",
			"resolve": _from_query("CRM Task", _task_filters),
			"linked": _linked("CRM Task", _task_filters),
		},
	],
}
