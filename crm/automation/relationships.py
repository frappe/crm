# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""The CRM relationships the schema can't derive on its own.

Everything backed by a Link, a child-table Link or a Dynamic Link is already offered by the
engine's schema provider, so this file only carries the edges that need a judgement call —
plus a few renames, which say nothing but "call this one `deals`, not `crm_deal_via_lead`".
Renamed entries are still resolved by the schema provider, so they can't drift from the
fields behind them.
"""

import frappe
from frappe.automation_engine.relationships import AutomationRelationshipProvider

COMMUNICATION_REFERENCE_DOCTYPES = ["CRM Lead", "CRM Deal"]


class CRMRelationshipProvider(AutomationRelationshipProvider):
	def get_definitions(self, source_doctype: str) -> list[dict]:
		return [_public(definition) for definition in DEFINITIONS.get(source_doctype, [])]

	def resolve(self, source_doc, relationship: str, params: dict) -> list[dict]:
		return _definition(source_doc.doctype, relationship)["resolve"](source_doc)

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


def _communication_filters(doc):
	return [["reference_doctype", "=", doc.doctype], ["reference_name", "=", doc.name]]


def _task_filters(doc):
	return [["reference_doctype", "=", doc.doctype], ["reference_docname", "=", doc.name]]


def _dynamic_reference(name, label, doctype, filters) -> dict:
	"""Dynamic references aren't derived — which DocTypes a reference pair points at is a fact
	about data, not schema — so the CRM names the ones it cares about."""
	return {
		"name": name,
		"label": label,
		"cardinality": "many",
		"target_doctype": doctype,
		"resolve": lambda doc: _references(
			doctype, frappe.get_all(doctype, filters=filters(doc), pluck="name")
		),
		"linked": lambda doc: (doctype, filters(doc)),
	}


def _communications() -> dict:
	return _dynamic_reference("communications", "Communications", "Communication", _communication_filters)


def _tasks() -> dict:
	return _dynamic_reference("tasks", "Tasks", "CRM Task", _task_filters)


def _communication_reference(doc) -> list[dict]:
	"""A Communication can reference anything on the site; a CRM flow only means these two."""
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


def _rename(name, derived_from, label) -> dict:
	return {"name": name, "derived_from": derived_from, "label": label}


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
		_communications(),
		_tasks(),
		_rename("deals", "crm_deal_via_lead", "Deals"),
	],
	"CRM Deal": [
		_communications(),
		_tasks(),
		_rename("contacts", "contacts_contact", "Contacts"),
	],
}
