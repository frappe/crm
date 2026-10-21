# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""CRM setup actions for Flow's assistant; loaded only when Flow is installed (see hooks.flow_tools)."""

import json
import re
from typing import Any, Literal

import frappe
from flow import ToolContext, tool
from frappe import _
from pydantic import BaseModel

FIELD_TYPES = {
	"short text": "Data",
	"long text": "Small Text",
	"number": "Int",
	"amount": "Currency",
	"date": "Date",
	"dropdown": "Select",
	"yes/no": "Check",
}


# a simple form's fields when none are given: name, email, phone and company
DEFAULT_FORM_FIELDS = [
	{"field": "first_name", "label": "First name", "required": True},
	{"field": "last_name", "label": "Last name", "required": False},
	{"field": "email", "label": "Email", "required": True},
	{"field": "mobile_no", "label": "Phone", "required": False},
	{"field": "organization", "label": "Company", "required": False},
]


class FormField(BaseModel):
	# a lead field, or a layout break where the form starts a new column or section
	field: str | None = None
	layout: Literal["column break", "section break"] | None = None
	label: str | None = None
	required: bool = False


class NewField(BaseModel):
	label: str
	kind: Literal["short text", "long text", "number", "amount", "date", "dropdown", "yes/no"]
	choices: list[str] = []


@tool
def setup_status(*, ctx: ToolContext) -> dict[str, Any]:
	"""Everything the CRM setup checklist needs, in one read: currency, stages, email, forms, team,
	lead assignment, data, and which sample records are left (None once cleared). Needs no approval."""
	from crm.demo.api import get_demo_state

	users = frappe.get_list(
		"User",
		filters={"user_type": "System User", "enabled": 1, "name": ["not in", ["Administrator", "Guest"]]},
		pluck="name",
	)
	return {
		"currency": frappe.db.get_single_value("FCRM Settings", "currency"),
		"deal_stages": frappe.get_list(
			"CRM Deal Status", fields=["name", "type", "probability"], order_by="position asc"
		),
		"lead_sources": frappe.get_list("CRM Lead Source", pluck="name"),
		"lost_reasons": frappe.get_list("CRM Lost Reason", pluck="name"),
		"email_accounts": frappe.get_list(
			"Email Account",
			fields=[
				"email_id",
				"enable_incoming",
				"enable_outgoing",
				"default_incoming",
				"default_outgoing",
				"create_lead_from_incoming_email",
			],
		),
		"email_templates": frappe.db.count("Email Template"),
		"web_forms": [
			{"title": f.title, "link": f"/crm-form/{f.route}", "published": f.published}
			for f in frappe.get_list(
				"Web Form",
				filters={"doc_type": ["in", ["CRM Lead", "CRM Deal"]]},
				fields=["title", "route", "published"],
				ignore_permissions=True,
			)
		],
		"ad_lead_syncing": frappe.db.count("Lead Sync Source", {"enabled": 1}),
		"users": [u for u in users if not u.endswith(".demo@example.com")],
		"invitations": frappe.get_list("CRM Invitation", fields=["email", "role", "status"]),
		"lead_assignment_rules": frappe.get_list(
			"Assignment Rule", filters={"document_type": "CRM Lead", "disabled": 0}, pluck="name"
		),
		"leads": frappe.db.count("CRM Lead"),
		"deals": frappe.db.count("CRM Deal"),
		"sample_data": _sample_data_left() if get_demo_state()["demo_data_created"] else None,
	}


def _sample_data_left() -> dict[str, Any]:
	"""The sample records the CRM made that still exist, by name, so nothing else is taken for one."""
	from crm.demo.api import DEMO_DEALS_KEY, DEMO_LEADS_KEY
	from crm.demo.users import DEMO_USER_EMAILS

	leads = json.loads(frappe.db.get_default(DEMO_LEADS_KEY) or "[]")
	deals = json.loads(frappe.db.get_default(DEMO_DEALS_KEY) or "{}").get("deals", [])
	return {
		"leads": frappe.get_all("CRM Lead", filters={"name": ["in", leads or [""]]}, pluck="name"),
		"deals": frappe.get_all("CRM Deal", filters={"name": ["in", deals or [""]]}, pluck="name"),
		"users": frappe.get_all("User", filters={"name": ["in", DEMO_USER_EMAILS]}, pluck="name"),
	}


def _bullets(lines: list[str]) -> str:
	return "\n".join(f"• {line}" for line in lines)


def _form_prompt(args: dict) -> str:
	verb = "Update" if args.get("form") else "Publish"
	fields = args.get("fields") or []
	if not fields:
		return (
			f'{verb} "{args.get("title")}" with the standard contact fields: name, email, phone and company.'
		)
	lines = []
	for f in fields:
		if f.get("layout") == "column break":
			lines.append("— next column —")
		elif f.get("layout") == "section break":
			lines.append(f"— new section{': ' + f['label'] if f.get('label') else ''} —")
		else:
			lines.append(f"{f.get('label') or f.get('field')}{' (required)' if f.get('required') else ''}")
	count = sum(1 for f in fields if not f.get("layout"))
	return f'{verb} "{args.get("title")}" with these {count} fields:\n' + "\n".join(
		line if line.startswith("—") else f"• {line}" for line in lines
	)


@tool(requires_confirmation=True, confirm_prompt=_form_prompt)
def publish_web_form(
	title: str,
	fields: list[FormField] | None = None,
	description: str = "",
	success_message: str = "Thanks, we'll be in touch soon.",
	form: str | None = None,
	*,
	ctx: ToolContext,
) -> dict[str, Any]:
	"""Create and publish a website form whose submissions become CRM leads, or update one: pass
	its name as `form` to change it in place, keeping its link. `fields` are in the order visitors
	see them: each a lead `field` with the `label` to show and whether it's `required`, or a
	`layout` break ("column break" starts the next column, "section break" a new block of fields).
	Use breaks only where the form changes layout. Leave `fields` out for the standard contact
	fields. Returns the form's link."""
	from crm.api.form import get_form_config, save_form

	current = get_form_config(form) if form else None
	data = {
		"title": title,
		"route": current["route"]
		if current
		else _free_route(frappe.scrub(title).replace("_", "-") or "contact-us"),
		"document_type": "CRM Lead",
		"description": description,
		"success_message": success_message,
		"published": 1,
		"fields": [_form_row(f, i) for i, f in enumerate(fields or DEFAULT_FORM_FIELDS)],
	}
	if current:
		# an update keeps the form's hidden defaults, which a save without them would clear
		data["hidden_fields"] = current["hidden_fields"]
	saved = save_form(form, data)
	return {"form": saved["name"], "link": f"/crm-form/{saved['route']}"}


def _form_row(f: FormField | dict, i: int) -> dict[str, Any]:
	f = f if isinstance(f, FormField) else FormField(**f)
	if f.layout:
		kind = "Column Break" if f.layout == "column break" else "Section Break"
		return {
			"fieldname": f"{frappe.scrub(kind)}_{i}",
			"fieldtype": kind,
			"label": f.label or "",
			"reqd": 0,
			"placeholder": "",
		}
	return {"fieldname": f.field, "label": f.label, "reqd": int(f.required), "placeholder": ""}


def _free_route(route: str) -> str:
	candidate, n = route, 2
	while frappe.db.exists("Web Form", {"route": candidate}):
		candidate, n = f"{route}-{n}", n + 1
	return candidate


# where a field can show on a record's page, and the CRM Fields Layout type behind each place
LAYOUT_PLACES = {"side panel": "Side Panel", "data tab": "Data Fields", "new record form": "Quick Entry"}


def _check_doctype(doctype: str) -> None:
	"""Fields go only on CRM records, which are the doctypes with a page layout."""
	if not frappe.db.exists("CRM Fields Layout", {"dt": doctype}):
		doctypes = frappe.get_all("CRM Fields Layout", pluck="dt", distinct=True, order_by="dt")
		frappe.throw(_("{0} has no page in the CRM. Pick one of: {1}").format(doctype, ", ".join(doctypes)))


def _fields_prompt(args: dict) -> str:
	lines = []
	for f in args.get("fields") or []:
		kind = f.get("kind")
		if kind == "dropdown":
			kind = f"dropdown with {', '.join(f.get('choices') or [])}"
		lines.append(f"{f.get('label')}: {kind}")
	count = f"{len(lines)} new field{'s' if len(lines) != 1 else ''}"
	return f"Add {count} to {_(args.get('doctype'))} records:\n{_bullets(lines)}"


@tool(requires_confirmation=True, confirm_prompt=_fields_prompt)
def add_fields(doctype: str, fields: list[NewField], *, ctx: ToolContext) -> dict[str, Any]:
	"""Add new fields to a CRM record type (`doctype`, such as CRM Lead, CRM Deal, Contact or CRM
	Organization), for example answers a website form collects. Use this, not a Custom Field record.
	A dropdown needs its choices. Returns each new field's fieldname. New fields show on no page
	until show_fields puts them there, so ask the user where to show them."""
	_check_doctype(doctype)
	meta = frappe.get_meta(doctype)
	added = {}
	for f in fields:
		f = f if isinstance(f, NewField) else NewField(**f)
		fieldname = (
			re.sub(r"_+", "_", re.sub(r"[^a-z0-9_]", "", frappe.scrub(f.label)))[:40].strip("_") or "field"
		)
		if meta.has_field(fieldname) or meta.has_field(f"custom_{fieldname}"):
			frappe.throw(_("{0} already has a field called {1}.").format(_(doctype), f.label))
		doc = frappe.get_doc(
			{
				"doctype": "Custom Field",
				"dt": doctype,
				"fieldname": fieldname,
				"label": f.label,
				"fieldtype": FIELD_TYPES[f.kind],
				"options": "\n".join(f.choices) if f.kind == "dropdown" else None,
			}
		).insert()
		added[f.label] = doc.fieldname
	return {"added": added}


def _show_prompt(args: dict) -> str:
	doctype = args.get("doctype")
	meta = frappe.get_meta(doctype)
	labels = [meta.get_label(f) for f in args.get("fields") or []]
	if args.get("after"):
		places = " and ".join(args.get("places") or ["places they show"])
		after = meta.get_label(args["after"])
		return f"On {_(doctype)} records, put these fields right after {after} in the {places}:\n{_bullets(labels)}"
	places = " and ".join(args.get("places") or ["side panel"])
	section = args.get("section") or "More details"
	return f'Show these fields on {_(doctype)} records, in a "{section}" section of the {places}:\n{_bullets(labels)}'


@tool(requires_confirmation=True, confirm_prompt=_show_prompt)
def show_fields(
	doctype: str,
	fields: list[str],
	places: list[Literal["side panel", "data tab", "new record form"]] | None = None,
	section: str = "More details",
	after: str | None = None,
	*,
	ctx: ToolContext,
) -> dict[str, list[str]]:
	"""Show fields (fieldnames, such as ones add_fields returned) on a CRM record's page, or move
	them: the side panel, the Data tab or the form for a new record. Without `after`, they go in the
	section called `section`, made if missing, and a field already shown stays where it is. With
	`after` (a fieldname), they go right after that field, moved from wherever they were; leave out
	`places` to move them only where they already show. Not every record type has every place:
	`not_available` lists the ones it lacks, and `after_missing` those where `after` isn't shown.
	Returns the places changed."""
	from frappe.utils import random_string

	_check_doctype(doctype)
	changed, not_available, after_missing = [], [], []
	for place in places or (list(LAYOUT_PLACES) if after else ["side panel"]):
		name = frappe.db.exists("CRM Fields Layout", {"dt": doctype, "type": LAYOUT_PLACES[place]})
		if not name:
			not_available.append(place)
			continue
		doc = frappe.get_doc("CRM Fields Layout", name)
		layout = json.loads(doc.layout or "[]")
		# Data Fields may be tabs of sections; the others are a list of sections
		tabs = layout if layout and "sections" in layout[0] else [{"sections": layout}]
		columns = [col for tab in tabs for sec in tab.get("sections", []) for col in sec.get("columns", [])]
		shown = {f for col in columns for f in col.get("fields", [])}
		if after:
			fields_before = {id(col): list(col.get("fields", [])) for col in columns}
			# without `places`, a field moves only where it already shows
			moving = [f for f in fields if f != after and (places or f in shown)]
			if not moving:
				continue
			target = next((col for col in columns if after in col.get("fields", [])), None)
			if not target:
				after_missing.append(place)
				continue
			for col in columns:
				col["fields"] = [f for f in col.get("fields", []) if f not in moving]
			i = target["fields"].index(after) + 1
			target["fields"][i:i] = moving
			# drop the sections the move left empty, but not ones that were empty before
			for tab in tabs:
				tab["sections"][:] = [
					sec
					for sec in tab.get("sections", [])
					if not sec.get("columns")
					or any(col.get("fields") for col in sec["columns"])
					or not any(set(fields_before[id(col)]) & set(moving) for col in sec["columns"])
				]
		else:
			new = [f for f in fields if f not in shown]
			if not new:
				continue
			sections = tabs[0]["sections"]
			existing = next(
				(sec for sec in sections if sec.get("label") == section and sec.get("columns")), None
			)
			if existing:
				existing["columns"][0].setdefault("fields", []).extend(new)
			else:
				sections.append(
					{
						"label": section,
						"name": f"section_{random_string(4)}",
						"opened": True,
						"columns": [{"name": f"column_{random_string(4)}", "fields": new}],
					}
				)
		doc.layout = json.dumps(layout)
		doc.save()
		changed.append(place)
	return {"shown_in": changed, "not_available": not_available, "after_missing": after_missing}


@tool(
	requires_confirmation=True,
	confirm_prompt=lambda args: (
		f"Connect {args.get('email')} ({args.get('provider')}) to the CRM, for sending and receiving, "
		"and make it the default. The password stays on your site."
	),
)
def connect_email(
	provider: Literal["GMail", "Outlook", "Yahoo", "Yandex"], email: str, password: str, *, ctx: ToolContext
) -> str:
	"""Connect a mailbox for sending and receiving. `password` is the secret: reference the chat's
	password box returned, never the password itself."""
	from flow.lib.secrets import reveal

	from crm.api.settings import create_email_account

	create_email_account(
		{
			"service": provider,
			"email_id": email,
			"email_account_name": email,
			"password": reveal(password),
			"enable_incoming": 1,
			"enable_outgoing": 1,
			"default_incoming": 1,
			"default_outgoing": 1,
		}
	)
	return f"Connected {email}."


def _convert_prompt(args: dict) -> str:
	name = frappe.db.get_value("CRM Lead", args.get("lead"), "lead_name") or args.get("lead")
	value = f" worth {args['deal_value']}" if args.get("deal_value") else ""
	return (
		f"Convert {name} ({args.get('lead')}) to a deal{value}. Their contact and organization come "
		"along, with the lead's notes, emails and tasks."
	)


@tool(requires_confirmation=True, confirm_prompt=_convert_prompt)
def convert_lead(lead: str, deal_value: float | None = None, *, ctx: ToolContext) -> dict[str, str]:
	"""Convert a lead to a deal the way the CRM's Convert to Deal button does: it creates or links the
	contact and organization and carries the lead's notes, emails and tasks over. Returns the deal's
	name and link. A lead already converted returns its existing deal."""
	from crm.fcrm.doctype.crm_lead.crm_lead import convert_to_deal

	deal = convert_to_deal(
		lead=lead,
		deal={"deal_value": deal_value} if deal_value else None,
		if_converted="Return Existing",
	)
	return {"deal": deal, "link": f"/crm/deals/{deal}"}


def _invite_prompt(args: dict) -> str:
	return f"Invite these people to the CRM as {args.get('role')}s:\n{_bullets(args.get('emails') or [])}"


@tool(requires_confirmation=True, confirm_prompt=_invite_prompt)
def invite_team(
	emails: list[str], role: Literal["Sales User", "Sales Manager", "System Manager"], *, ctx: ToolContext
) -> dict[str, list[str]]:
	"""Email an invitation to join the CRM to each address, all with the same role. Returns who was
	invited, and who was skipped because they're already on the CRM or already invited."""
	from crm.api import invite_by_email

	result = invite_by_email(",".join(emails), role) or {}
	# people already on the CRM or already invited are skipped, so say who actually got one
	return {
		"invited": result.get("to_invite", []),
		"already_on_the_crm": result.get("existing_members", []),
		"already_invited": result.get("existing_invites", []),
	}


def _assign_prompt(args: dict) -> str:
	how = "taking turns" if args.get("rule") == "Round Robin" else "to whoever has the fewest"
	return f"Hand out new leads to these people, {how}:\n{_bullets(args.get('users') or [])}"


@tool(requires_confirmation=True, confirm_prompt=_assign_prompt)
def assign_new_leads(
	users: list[str], rule: Literal["Round Robin", "Load Balancing"] = "Round Robin", *, ctx: ToolContext
) -> str:
	"""Assign each new lead automatically to one of `users` (their user emails)."""
	name, n = "New leads", 2
	while frappe.db.exists("Assignment Rule", name):
		name, n = f"New leads {n}", n + 1
	frappe.get_doc(
		{
			"doctype": "Assignment Rule",
			"name": name,
			"assignment_rule_name": name,
			"document_type": "CRM Lead",
			"rule": rule,
			"priority": 1,
			"users": [{"user": user} for user in users],
			"assign_condition": 'status == "New"',
			"assign_condition_json": '[["status","==","New"]]',
			"description": "Hands out new leads to the sales team.",
			"assignment_days": [
				{"day": day}
				for day in ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")
			],
		}
	).insert()
	return f"Created the assignment rule {name}."


@tool(
	requires_confirmation=True,
	confirm_prompt=lambda args: f"Set the CRM currency to {args.get('currency')}. It can't be changed later.",
)
def set_currency(currency: str, *, ctx: ToolContext) -> str:
	"""Set the currency deal values are in, such as INR or USD. It can only be set once."""
	if not frappe.db.exists("Currency", currency):
		frappe.throw(_("There's no currency {0}.").format(currency))
	settings = frappe.get_single("FCRM Settings")
	if settings.currency:
		frappe.throw(_("The currency is already set to {0}.").format(settings.currency))
	settings.currency = currency
	settings.save()
	return f"Currency set to {currency}."


@tool(
	requires_confirmation=True,
	confirm_prompt=lambda args: "Remove the sample leads, deals, notes, tasks and demo users that came with the CRM. Anything you added stays.",
)
def clear_sample_data(*, ctx: ToolContext) -> str:
	"""Remove the sample data a new CRM starts with."""
	from crm.demo.api import clear_demo_data

	clear_demo_data()
	return "Sample data removed."
