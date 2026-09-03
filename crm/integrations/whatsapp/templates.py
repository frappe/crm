# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""WhatsApp message templates, managed from the CRM.

Outside the 24-hour window that opens when a customer writes, WhatsApp only
allows **approved templates**, so creating them cannot be a trip into the Desk:
it belongs in the CRM next to the chat.

frappe_whatsapp owns the `WhatsApp Templates` doctype and submits each one to
Meta for review when it is saved; this module is the CRM-facing surface over it.
Field names are read from the installed doctype rather than assumed, so a
different frappe_whatsapp release degrades instead of breaking.
"""

import json

import frappe
from frappe import _

MANAGER_ROLES = {"System Manager", "Sales Manager"}
EDITABLE_FIELDS = ("template_name", "category", "language_code", "header", "template", "footer")


def _check_manager():
	if not MANAGER_ROLES & set(frappe.get_roles()):
		frappe.throw(_("Only sales managers can manage WhatsApp templates"), frappe.PermissionError)


def templates_available() -> bool:
	return bool(frappe.db.exists("DocType", "WhatsApp Templates"))


def _known_fields() -> set[str]:
	return {df.fieldname for df in frappe.get_meta("WhatsApp Templates").fields}


def _options_for(fieldname: str) -> list[str]:
	"""Select options straight from the installed doctype."""
	meta = frappe.get_meta("WhatsApp Templates")
	field = meta.get_field(fieldname)
	if not field or field.fieldtype != "Select" or not field.options:
		return []
	return [option for option in field.options.split("\n") if option]


@frappe.whitelist()
def get_templates() -> dict:
	_check_manager()
	if not templates_available():
		return {"available": False, "templates": []}

	known = _known_fields()
	fields = ["name"] + [f for f in ("template_name", "status", *EDITABLE_FIELDS) if f in known]
	return {
		"available": True,
		"templates": frappe.get_all(
			"WhatsApp Templates", fields=list(dict.fromkeys(fields)), order_by="modified desc"
		),
		"categories": _options_for("category") or ["MARKETING", "UTILITY", "AUTHENTICATION"],
		"languages": _options_for("language_code") or ["en", "en_US", "it"],
		"fields": sorted(known & set(EDITABLE_FIELDS)),
	}


@frappe.whitelist(methods=["POST"])
def save_template(template: dict | str, name: str | None = None) -> dict:
	"""Create or update a template. Saving submits it to Meta for review."""
	_check_manager()
	if not templates_available():
		frappe.throw(_("The WhatsApp app is not installed on this site"))
	if isinstance(template, str):
		template = json.loads(template)

	known = _known_fields()
	values = {
		field: template.get(field)
		for field in EDITABLE_FIELDS
		if field in known and template.get(field) is not None
	}
	if not values.get("template"):
		frappe.throw(_("The message body is required"))
	if not name and not values.get("template_name"):
		frappe.throw(_("A template name is required"))

	if name:
		doc = frappe.get_doc("WhatsApp Templates", name)
		# Meta does not allow renaming an approved template
		values.pop("template_name", None)
		doc.update(values)
		doc.save()
	else:
		doc = frappe.get_doc({"doctype": "WhatsApp Templates", **values})
		doc.insert()
	return {"name": doc.name, "status": doc.get("status") or ""}


@frappe.whitelist(methods=["POST"])
def delete_template(name: str) -> None:
	_check_manager()
	frappe.delete_doc("WhatsApp Templates", name)
