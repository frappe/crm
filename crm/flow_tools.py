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
	from crm.demo.users import DEMO_USER_EMAILS

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
		"users": [u for u in users if u not in DEMO_USER_EMAILS],
		"invitations": frappe.get_list("CRM Invitation", fields=["email", "role", "status"]),
		"lead_assignment_rules": frappe.get_list(
			"Assignment Rule", filters={"document_type": "CRM Lead", "disabled": 0}, pluck="name"
		),
		"leads": frappe.db.count("CRM Lead"),
		"deals": frappe.db.count("CRM Deal"),
		"sample_data": _sample_data_left() if get_demo_state()["demo_data_created"] else None,
		"automations": frappe.get_list(
			"Automation Flow",
			filters={"document_type": ["in", ["CRM Lead", "CRM Deal"]]},
			fields=["title", "enabled"],
		)
		if frappe.has_permission("Automation Flow")
		else None,
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
	if not fields and args.get("form"):
		return f'Update "{args.get("title")}". Its fields and other settings stay as they are.'
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
	description: str | None = None,
	success_message: str | None = None,
	form: str | None = None,
	*,
	ctx: ToolContext,
) -> dict[str, Any]:
	"""Create and publish a website form whose submissions become CRM leads, or update one: pass
	its name as `form` to change it in place, keeping its link. `fields` are in the order visitors
	see them: each a lead `field` with the `label` to show and whether it's `required`, or a
	`layout` break ("column break" starts the next column, "section break" a new block of fields).
	Use breaks only where the form changes layout. Leave `fields` out for the standard contact
	fields on a new form; on an update, anything left out stays as it is. Returns the form's link."""
	from crm.api.form import get_form_config, save_form

	if form:
		# an update starts from the saved form, so its layout and settings stay unless replaced
		data = {k: v for k, v in get_form_config(form).items() if k not in ("name", "fields")}
		data.update(title=title, published=1)
	else:
		data = {
			"title": title,
			"route": _free_route(frappe.scrub(title).replace("_", "-") or "contact-us"),
			"document_type": "CRM Lead",
			"description": "",
			"success_message": "Thanks, we'll be in touch soon.",
			"published": 1,
		}
		fields = fields or DEFAULT_FORM_FIELDS
	if description is not None:
		data["description"] = description
	if success_message is not None:
		data["success_message"] = success_message
	if fields:
		data["fields"] = [_form_row(f, i) for i, f in enumerate(fields)]
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


# sections the CRM hides or removes on its own, which a field put there would vanish with
AUTO_SECTIONS = {
	("CRM Lead", "side panel"): {"lost_reason_section"},
	("CRM Deal", "side panel"): {"lost_reason_section"},
	("CRM Deal", "new record form"): {
		"organization_section",
		"organization_details_section",
		"contact_section",
		"contact_details_section",
	},
}


def _tabs(layout: list) -> list[dict]:
	# Data Fields may be tabs of sections; the others are a list of sections
	return layout if layout and "sections" in layout[0] else [{"sections": layout}]


def _section_fields(sec: dict) -> set[str]:
	return {f for col in sec.get("columns", []) for f in col.get("fields", [])}


def _new_section(label: str, fields: list[str]) -> dict[str, Any]:
	from frappe.utils import random_string

	return {
		"label": label,
		"name": f"section_{random_string(4)}",
		"opened": True,
		"columns": [{"name": f"column_{random_string(4)}", "fields": fields}],
	}


def _shown_in(doctype: str, fields: list[str]) -> list[str]:
	"""The places on a record's page where any of `fields` shows."""
	places = []
	for place, kind in LAYOUT_PLACES.items():
		layout = json.loads(
			frappe.db.get_value("CRM Fields Layout", {"dt": doctype, "type": kind}, "layout") or "[]"
		)
		if any(
			set(fields) & _section_fields(sec) for tab in _tabs(layout) for sec in tab.get("sections", [])
		):
			places.append(place)
	return places


def _show_prompt(args: dict) -> str:
	doctype = args.get("doctype")
	meta = frappe.get_meta(doctype)
	labels = [meta.get_label(f) for f in args.get("fields") or []]
	if args.get("after"):
		shown = args.get("places") or _shown_in(doctype, args.get("fields") or [])
		places = " and ".join(shown or ["places they show"])
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
	`places` to move them only where they already show. A section the CRM hides or removes on its
	own, such as Lost Reason, takes no other fields: they go in a new `section` right after it.
	Not every record type has every place: `not_available` lists the ones it lacks, and
	`after_missing` those where `after` isn't shown. Returns the places changed."""
	_check_doctype(doctype)
	changed, not_available, after_missing = [], [], []
	for place in places or (list(LAYOUT_PLACES) if after else ["side panel"]):
		name = frappe.db.exists("CRM Fields Layout", {"dt": doctype, "type": LAYOUT_PLACES[place]})
		if not name:
			not_available.append(place)
			continue
		doc = frappe.get_doc("CRM Fields Layout", name)
		layout = json.loads(doc.layout or "[]")
		tabs = _tabs(layout)
		auto = AUTO_SECTIONS.get((doctype, place), set())
		columns = [col for tab in tabs for sec in tab.get("sections", []) for col in sec.get("columns", [])]
		shown = {f for col in columns for f in col.get("fields", [])}
		if after:
			fields_before = {id(col): list(col.get("fields", [])) for col in columns}
			# without `places`, a field moves only where it already shows
			moving = [f for f in fields if f != after and (places or f in shown)]
			if not moving:
				continue
			found = next(
				(
					(tab, sec, col)
					for tab in tabs
					for sec in tab.get("sections", [])
					for col in sec.get("columns", [])
					if after in col.get("fields", [])
				),
				None,
			)
			if not found:
				after_missing.append(place)
				continue
			tab, target_sec, target = found
			# only fields already in a section the CRM hides or removes stay in it
			inside = _section_fields(target_sec) if target_sec.get("name") in auto else set(moving)
			for col in columns:
				col["fields"] = [f for f in col.get("fields", []) if f not in moving]
			i = target["fields"].index(after) + 1
			target["fields"][i:i] = [f for f in moving if f in inside]
			if outside := [f for f in moving if f not in inside]:
				sections = tab["sections"]
				sections.insert(sections.index(target_sec) + 1, _new_section(section, outside))
			# drop the sections the move left empty, but not ones that were empty before
			for tab in tabs:
				tab["sections"][:] = [
					sec
					for sec in tab.get("sections", [])
					if not sec.get("columns")
					or any(col.get("fields") for col in sec["columns"])
					or not any(set(fields_before.get(id(col), [])) & set(moving) for col in sec["columns"])
				]
		else:
			new = [f for f in fields if f not in shown]
			if not new:
				continue
			sections = tabs[0]["sections"]
			existing = next(
				(
					sec
					for sec in sections
					if sec.get("label") == section and sec.get("columns") and sec.get("name") not in auto
				),
				None,
			)
			if existing:
				existing["columns"][0].setdefault("fields", []).extend(new)
			else:
				sections.append(_new_section(section, new))
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
	from crm.api.form import _default_status

	# new leads are the ones still at the status a lead starts with on this site
	status = _default_status("CRM Lead")
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
			"assign_condition": f"status == {json.dumps(status)}",
			"assign_condition_json": json.dumps([["status", "==", status]]),
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
	# the site-wide default too, which Settings > Defaults shows, unless someone already chose one
	if not frappe.db.get_single_value("System Settings", "currency"):
		frappe.db.set_single_value("System Settings", "currency", currency)
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


# what an automation starts on: a change to the record, or a CRM event about it
RECORD_EVENTS = {
	"replied": "crm.prospect_message_received",
	"emailed": "crm.prospect_message_sent",
	"qualified": "crm.lead_qualified",
	"converted": "crm.lead_converted",
	"won": "crm.deal_won",
	"lost": "crm.deal_lost",
	"task overdue": "crm.task_overdue",
}
LEAD_ONLY = {"qualified", "converted"}
LEAD_STEPS = {"convert to deal", "add to score", "set temperature"}
DEAL_ONLY = {"won", "lost"}
RECORDS = {"lead": "CRM Lead", "deal": "CRM Deal"}
OPERATORS = {
	"is": "=",
	"is not": "!=",
	"is more than": ">",
	"is less than": "<",
	"contains": "like",
	"does not contain": "not like",
	"ends with": "like",
}
LIKE_VALUES = {"contains": "%{}%", "does not contain": "%{}%", "ends with": "%{}"}
WAIT_UNITS = {"minutes": "Minutes", "hours": "Hours", "days": "Days"}
# people to tell or hand work to; anyone else is named by their user email
PEOPLE = {"assigned": "@assignees", "created by": "@owner"}


class Condition(BaseModel):
	field: str
	op: Literal[
		"is", "is not", "is more than", "is less than", "contains", "does not contain", "ends with"
	] = "is"
	value: str


class AutomationStep(BaseModel):
	# "stop if they replied" ends the run when the lead or deal sent an email since it started,
	# so the steps after it only happen when nobody replied
	do: Literal[
		"notify",
		"email the team",
		"email them",
		"create task",
		"assign",
		"set field",
		"wait",
		"stop if they replied",
		"convert to deal",
		"add to score",
		"set temperature",
	]
	# this step happens only for records that match, such as -5 when the email ends with gmail.com
	only_if: list[Condition] = []
	people: list[str] = []
	text: str = ""
	message: str = ""
	email_template: str | None = None
	field: str | None = None
	value: str | None = None
	amount: int = 0
	unit: Literal["minutes", "hours", "days"] = "days"


def _automation_prompt(args: dict) -> str:
	lines = [_plain_placeholders(line) for line in _describe_automation(args)]
	return f'Add the automation "{args.get("name")}":\n' + _bullets(lines)


def _plain_placeholders(text: str) -> str:
	"""{{ doc.lead_name }} reads as [lead name] on the approval card."""
	return re.sub(r"\{\{\s*doc\.(\w+)[^}]*\}\}", lambda m: f"[{m[1].replace('_', ' ')}]", text)


def _describe_automation(args: dict) -> list[str]:
	record = args.get("record") or "lead"
	meta = frappe.get_meta(RECORDS.get(record, "CRM Lead"))

	def label(fieldname):
		field = meta.get_field(fieldname or "")
		return (field.label if field else fieldname or "").lower()

	starts = {
		"created": f"a new {record} is added",
		"changed": f"a {record}'s {label(args.get('field') or 'status')} changes"
		+ (f" to {args['to_value']}" if args.get("to_value") else ""),
		"replied": f"a {record} replies to an email",
		"emailed": f"someone on the team emails a {record}",
		"qualified": "a lead is qualified",
		"converted": "a lead becomes a deal",
		"won": "a deal is won",
		"lost": "a deal is lost",
		"task overdue": f"a task on a {record} goes overdue",
		"date": f"it's {_days(args.get('days'))} {args.get('direction') or 'before'} a {record}'s "
		f"{label(args.get('date_field'))}",
	}
	lines = [f"When {starts.get(args.get('when'), args.get('when'))}"]
	if args.get("only_if"):
		conditions = [c if isinstance(c, dict) else c.model_dump() for c in args["only_if"]]
		lines.append(f"Only if its {_describe_conditions(conditions, label)}")
	for s in args.get("steps") or []:
		s = s if isinstance(s, dict) else s.model_dump()
		conditions = [c if isinstance(c, dict) else c.model_dump() for c in s.get("only_if") or []]
		step = _describe_step(s, label)
		if conditions:
			step = f"If its {_describe_conditions(conditions, label)}: {step[0].lower()}{step[1:]}"
		lines.append(step)
	return lines


def _describe_conditions(conditions: list[dict], label) -> str:
	return " and ".join(f"{label(c['field'])} {c.get('op') or 'is'} {c['value']}" for c in conditions)


def _days(n) -> str:
	return f"{n or 0} day" + ("" if n == 1 else "s")


def _describe_people(people: list[str]) -> str:
	names = {"me": "you", "assigned": "whoever it's assigned to", "created by": "whoever added it"}
	return (
		", ".join(names.get(p) or frappe.db.get_value("User", p, "full_name") or p for p in people)
		or "nobody"
	)


def _describe_step(s: dict, label) -> str:
	people = _describe_people(s.get("people") or [])
	due = "today" if not s.get("amount") else f"in {_days(s.get('amount'))}"
	return {
		"notify": f'Notify {people} in the CRM: "{s.get("text")}"',
		"email the team": f'Email {people}: "{s.get("text")}"',
		"email them": f'Email them: "{s.get("email_template") or s.get("text")}"',
		"create task": f'Add the task "{s.get("text")}", due {due}',
		"assign": f"Assign it to {people}",
		"set field": f"Set its {label(s.get('field'))} to {s.get('value')}",
		"wait": f"Wait {s.get('amount')} {s.get('unit') or 'days'}",
		"stop if they replied": "Stop here if they've replied",
		"convert to deal": "Convert the lead to a deal",
		"add to score": _describe_score(s),
		"set temperature": f"Mark it {s.get('value')}",
	}[s["do"]]


def _describe_score(s: dict) -> str:
	amount = s.get("amount") or 0
	change = f"Add {amount} to its score" if amount >= 0 else f"Take {-amount} off its score"
	return change + (f' ("{s["text"]}")' if s.get("text") else "")


@tool(requires_confirmation=True, confirm_prompt=_automation_prompt)
def add_automation(
	name: str,
	record: Literal["lead", "deal"],
	when: Literal[
		"created",
		"changed",
		"replied",
		"emailed",
		"qualified",
		"converted",
		"won",
		"lost",
		"task overdue",
		"date",
	],
	steps: list[AutomationStep],
	field: str = "status",
	to_value: str | None = None,
	date_field: str | None = None,
	days: int = 0,
	direction: Literal["before", "after"] = "before",
	only_if: list[Condition] | None = None,
	*,
	ctx: ToolContext,
) -> dict[str, Any]:
	"""Add a CRM workflow automation: when something happens to a lead or deal, run `steps` in
	order. `when`: "created"; "changed" (`field`, default status, optionally changing `to_value`);
	"replied" (they emailed back); "emailed" (someone on the team emailed them); "qualified" or
	"converted" (leads); "won" or "lost" (deals); "task overdue"; or "date" (`days` before or
	after the record's `date_field`). `only_if` limits it to records whose fields match.
	Steps: "notify" `people` in the CRM with `text` (and an optional `message`); "email the team"
	(`people`, `text` as subject, `message`); "email them" (the lead or deal, with an
	`email_template`, or `text` as subject and `message`); "create task" (`text` as the title, due
	in `amount` days, for the record's owner); "assign" to `people`; "set field" (`field`,
	`value`); "wait" (`amount` `unit`); "stop if they replied"; "convert to deal", "add to score"
	(`amount`, negative to take away, `text` as the reason) or "set temperature" (`value`, one of
	the lead's temperature choices), all three for leads. A step's own `only_if` makes just that step conditional, such
	as -5 when the email ends with gmail.com and +10 when it doesn't.
	`people` are user emails, "assigned" (whoever the record is assigned to) or "created by".
	Text can use the record's fields, such as {{ doc.lead_name }} or {{ doc.organization }}.
	Returns the automation and its link."""
	doctype = RECORDS[record]
	if (when in LEAD_ONLY or any(s.do in LEAD_STEPS for s in steps)) and record != "lead":
		frappe.throw(_("That only works on leads."))
	if when in DEAL_ONLY and record != "deal":
		frappe.throw(_("That only works on deals."))
	meta = frappe.get_meta(doctype)
	flow = {
		"doctype": "Automation Flow",
		"title": _free_automation_title(name),
		"document_type": doctype,
		"enabled": 1,
		"stop_on_error": 1,
		"actions": _automation_rows(steps, record, ctx.user),
	}
	if when == "created":
		flow["trigger_type"] = "Doc Created"
	elif when == "changed":
		_check_field(meta, field)
		flow.update(trigger_type="Field Value Changed", trigger_field=field, to_value=to_value)
	elif when == "date":
		if not date_field or meta.get_field(date_field) is None:
			frappe.throw(_("Pick a date field on the {0}.").format(record))
		flow.update(
			trigger_type="Date Based",
			date_field=date_field,
			date_offset=days,
			date_direction=direction.title(),
		)
	else:
		flow.update(trigger_type="Custom Event", custom_event=RECORD_EVENTS[when])
	for c in [*(only_if or []), *(c for s in steps for c in s.only_if)]:
		_check_field(meta, c.field)
	for s in steps:
		if s.do == "set temperature":
			_check_temperature(s.value)
	if only_if:
		flow["filters"] = json.dumps(
			[[c.field, OPERATORS[c.op], LIKE_VALUES.get(c.op, "{}").format(c.value)] for c in only_if]
		)
	saved = frappe.get_doc(flow).insert()
	return {
		"automation": saved.title,
		"name": saved.name,
		"link": f"/crm/leads?settings=Workflow%20Automations&record={saved.name}",
	}


def _check_temperature(value: str | None) -> None:
	from crm.automation.scoring import temperature_options

	choices = temperature_options()
	if value not in choices:
		frappe.throw(_("A lead's temperature can be {0}.").format(", ".join(choices)))


def _check_field(meta, fieldname: str) -> None:
	if meta.get_field(fieldname) is None and fieldname not in ("name", "owner"):
		record = "deal" if meta.name == "CRM Deal" else "lead"
		frappe.throw(_("There's no {0} field on the {1}.").format(fieldname, record))


def _free_automation_title(title: str) -> str:
	candidate, n = title, 2
	while frappe.db.exists("Automation Flow", {"title": candidate}):
		candidate, n = f"{title} {n}", n + 1
	return candidate


def _people(people: list[str], me: str) -> list[str]:
	return [me if p == "me" else PEOPLE.get(p, p) for p in people]


def _automation_rows(steps: list[AutomationStep], record: str, me: str) -> list[dict[str, Any]]:
	rows, branch_of = [], 0
	meta = frappe.get_meta(RECORDS[record])

	def add(row: dict[str, Any], parent: int) -> int:
		idx = len(rows) + 1
		if parent:
			row.update(parent_step=parent, branch="If")
		rows.append(
			{
				"idx": idx,
				"step_key": f"step_{idx}",
				"target": "trigger",
				**row,
				"params": json.dumps(row.get("params") or {}),
			}
		)
		return idx

	for s in steps:
		parent = branch_of
		if s.only_if:
			# the step sits in the If arm of its own condition, so other records skip just this step
			condition = _condition_expression(s.only_if, meta)
			parent = add({"step_type": "If", "step_condition": condition}, parent)
		if s.do == "stop if they replied":
			# the If arm holds every later step, so they only run when nothing came back
			branch_of = add(
				{"step_type": "If", "step_condition": "True", "related_condition": _no_reply_since_start()},
				parent,
			)
		elif s.do == "wait":
			add({"step_type": "Wait", "params": {"value": s.amount, "unit": WAIT_UNITS[s.unit]}}, parent)
		else:
			action_type, params = _automation_action(s, record, me)
			add({"step_type": "Action", "action_type": action_type, "params": params}, parent)
	return rows


def _condition_expression(conditions: list[Condition], meta) -> str:
	"""A step's conditions as the expression its If step checks: numbers compared as numbers, and
	text case-insensitively."""
	return " and ".join(_condition_part(c, meta) for c in conditions)


NUMBER_OPS = {"is": "==", "is not": "!=", "is more than": ">", "is less than": "<"}


def _condition_part(c: Condition, meta) -> str:
	from frappe.model import numeric_fieldtypes

	field = meta.get_field(c.field)
	is_number = field and field.fieldtype in numeric_fieldtypes
	if is_number or c.op in ("is more than", "is less than"):
		if c.op not in NUMBER_OPS:
			frappe.throw(
				_("{0} is a number: use is, is not, is more than or is less than.").format(field.label)
			)
		return f"float(doc.{c.field} or 0) {NUMBER_OPS[c.op]} {_number(c.value, field)}"
	text, value = f"(doc.{c.field} or '').lower()", repr(c.value.lower())
	return {
		"is": f"{text} == {value}",
		"is not": f"{text} != {value}",
		"contains": f"{value} in {text}",
		"does not contain": f"{value} not in {text}",
		"ends with": f"{text}.endswith({value})",
	}[c.op]


def _number(value: str, field) -> float:
	# a yes/no field holds 1 or 0
	if field and field.fieldtype == "Check":
		return 1.0 if value.strip().lower() in ("1", "yes", "true", "checked") else 0.0
	return frappe.utils.flt(value)


def _no_reply_since_start() -> str:
	return json.dumps(
		{
			"type": "RelatedNotExists",
			"source": "trigger",
			"relationship": "communications",
			"filters": [
				["sent_or_received", "=", "Received"],
				["creation", ">", "{{ context.run.creation }}"],
			],
		}
	)


def _automation_action(s: AutomationStep, record: str, me: str) -> tuple[str, dict[str, Any]]:
	if s.do == "notify":
		return "SendCRMNotification", {
			"recipients": _people(s.people, me),
			"notification_text": s.text,
			"message": s.message,
		}
	if s.do == "email the team":
		return "SendNotification", {
			"channel": "Email",
			"recipients": _people(s.people, me),
			"subject": s.text,
			"message": s.message,
		}
	if s.do == "email them":
		if s.email_template:
			return "SendCRMEmail", {"email_template": s.email_template}
		return "SendCRMEmail", {"subject": s.text, "message": s.message}
	if s.do == "create task":
		doctype = RECORDS[record]
		return "CreateDocument", {
			"doctype": "CRM Task",
			"values": {
				"title": s.text,
				"status": "Todo",
				"assigned_to": f"{{{{ doc.{record}_owner or '' }}}}",
				"reference_doctype": doctype,
				"reference_docname": "{{ doc.name }}",
				"due_date": f"{{{{ frappe.utils.add_days(frappe.utils.nowdate(), {s.amount}) }}}}",
			},
		}
	if s.do == "assign":
		return "AssignToUser", {"assign_to": _people(s.people, me), "description": s.text}
	if s.do == "set field":
		return "SetFieldValue", {"field": s.field, "value": s.value}
	if s.do == "add to score":
		return "AdjustLeadScore", {"amount": s.amount, "reason": s.text}
	if s.do == "set temperature":
		return "SetLeadTemperature", {"temperature": s.value}
	# convert to deal: a retry returns the same deal instead of making another, and sites with
	# forecasting get the placeholder value and closing date the rep then corrects
	from crm.automation.reference_flows import forecast_defaults

	return "ConvertLeadToDeal", {"if_converted": "Return Existing", "deal": forecast_defaults()}


# what a day and a pipeline look like, read with the user's own permissions and never changed
OPEN_TASK = ["not in", ["Done", "Canceled"]]
QUIET_DAYS = 14


@tool
def my_day(days: int = 1, *, ctx: ToolContext) -> dict[str, Any]:
	"""What the signed-in user has on today: their tasks due today or overdue, leads and deals of
	theirs waiting on a reply, their deals closing in the next 7 days or gone quiet for 2 weeks,
	and leads they got since yesterday. `days` widens the tasks to those due in that many days
	from today, such as 7 for the week. Each item has a `link`. Needs no approval."""
	user, today = ctx.user, frappe.utils.getdate()
	until = frappe.utils.add_days(today, min(max(days, 1), 31))
	leads = frappe.get_list(
		"CRM Lead",
		filters={"lead_owner": user, "converted": 0},
		fields=["name", "lead_name", "organization", "creation"],
		limit=500,
	)
	deals = _open_deals({"deal_owner": user})
	return {
		"tasks": [
			{**_record(t.reference_doctype, t.reference_docname), "task": t.title, "due": str(t.due_date)}
			for t in frappe.get_list(
				"CRM Task",
				filters={"assigned_to": user, "status": OPEN_TASK, "due_date": ["<", until]},
				fields=["title", "due_date", "reference_doctype", "reference_docname"],
				order_by="due_date asc",
				limit=50,
			)
		],
		"waiting_on_reply": _waiting_on_reply(
			[("CRM Lead", lead.name) for lead in leads] + [("CRM Deal", deal.name) for deal in deals]
		),
		"deals_closing_this_week": [
			{**_deal(d), "closes": str(d.expected_closure_date)}
			for d in deals
			if d.expected_closure_date and today <= d.expected_closure_date <= frappe.utils.add_days(today, 7)
		],
		"quiet_deals": [
			_deal(d)
			for d in deals
			if frappe.utils.getdate(d.modified) < frappe.utils.add_days(today, -QUIET_DAYS)
		][:10],
		"new_leads": [
			_lead(lead)
			for lead in leads
			if frappe.utils.getdate(lead.creation) >= frappe.utils.add_days(today, -1)
		],
	}


@tool
def sales_health(*, ctx: ToolContext) -> dict[str, Any]:
	"""How sales are going, for everything the user can see: open deals by stage with their value,
	this month against last month (new leads, leads turned into deals, deals won and lost),
	deals closing in the next 30 days, deals gone quiet for 2 weeks and overdue tasks. Values are
	in the CRM's currency. Needs no approval."""
	today = frappe.utils.getdate()
	this_month = frappe.utils.get_first_day(today)
	last_month = frappe.utils.add_months(this_month, -1)
	stages = frappe.get_all("CRM Deal Status", fields=["name", "type"], order_by="position asc")
	deals = _open_deals({})
	pipeline = []
	for stage in stages:
		if stage.type in ("Won", "Lost"):
			continue
		rows = [d for d in deals if d.status == stage.name]
		pipeline.append({"stage": stage.name, "deals": len(rows), "value": sum(_value(d) for d in rows)})
	return {
		"currency": frappe.db.get_single_value("FCRM Settings", "currency"),
		"open_pipeline": pipeline,
		"this_month": _month(this_month, today, stages),
		"last_month": _month(last_month, frappe.utils.add_days(this_month, -1), stages),
		"closing_soon": [
			{**_deal(d), "closes": str(d.expected_closure_date), "value": _value(d)}
			for d in sorted(
				(d for d in deals if d.expected_closure_date),
				key=lambda d: d.expected_closure_date,
			)
			if today <= d.expected_closure_date <= frappe.utils.add_days(today, 30)
		][:10],
		"quiet_deals": len(
			[d for d in deals if frappe.utils.getdate(d.modified) < frappe.utils.add_days(today, -QUIET_DAYS)]
		),
		"overdue_tasks": len(
			frappe.get_list(
				"CRM Task",
				filters={"status": OPEN_TASK, "due_date": ["<", today]},
				pluck="name",
				limit=1000,
			)
		),
	}


def _open_deals(filters: dict[str, Any]) -> list:
	closed = frappe.get_all("CRM Deal Status", filters={"type": ["in", ["Won", "Lost"]]}, pluck="name")
	return frappe.get_list(
		"CRM Deal",
		filters={**filters, "status": ["not in", closed or [""]]},
		fields=[
			"name",
			"organization",
			"lead_name",
			"status",
			"deal_value",
			"expected_deal_value",
			"exchange_rate",
			"expected_closure_date",
			"modified",
		],
		limit=1000,
	)


def _month(start, end, stages) -> dict[str, Any]:
	"""New leads, conversions, and deals won and lost between two dates."""
	won = [s.name for s in stages if s.type == "Won"] or [""]
	lost = [s.name for s in stages if s.type == "Lost"] or [""]
	between = ["between", [start, end]]
	won_deals = frappe.get_list(
		"CRM Deal",
		filters={"status": ["in", won], "closed_date": between},
		fields=["deal_value", "expected_deal_value", "exchange_rate"],
		limit=1000,
	)
	return {
		"new_leads": frappe.db.count("CRM Lead", {"creation": between}) if _can_read("CRM Lead") else None,
		"leads_turned_into_deals": len(
			frappe.get_list("CRM Deal", filters={"lead": ["is", "set"], "creation": between}, pluck="name")
		),
		"deals_won": len(won_deals),
		"won_value": sum(_value(d) for d in won_deals),
		"deals_lost": len(
			frappe.get_list(
				"CRM Deal", filters={"status": ["in", lost], "closed_date": between}, pluck="name"
			)
		),
	}


def _can_read(doctype: str) -> bool:
	return frappe.has_permission(doctype, "read")


def _value(deal) -> float:
	return (deal.deal_value or deal.expected_deal_value or 0) * (deal.exchange_rate or 1)


def _waiting_on_reply(records: list[tuple[str, str]]) -> list[dict[str, Any]]:
	"""Leads and deals whose latest email came from them, so the next move is ours."""
	waiting = []
	for doctype in ("CRM Lead", "CRM Deal"):
		names = [name for dt, name in records if dt == doctype]
		if not names:
			continue
		latest = {}
		for c in frappe.get_all(
			"Communication",
			filters={
				"reference_doctype": doctype,
				"reference_name": ["in", names],
				"communication_type": "Communication",
			},
			fields=["reference_name", "sent_or_received", "subject", "communication_date"],
			order_by="communication_date desc",
		):
			latest.setdefault(c.reference_name, c)
		waiting += [
			{**_record(doctype, name), "subject": c.subject, "since": str(c.communication_date)}
			for name, c in latest.items()
			if c.sent_or_received == "Received"
		]
	return waiting[:20]


def _record(doctype: str | None, name: str | None) -> dict[str, Any]:
	if doctype == "CRM Deal" and name:
		return _deal(
			frappe.db.get_value(
				"CRM Deal", name, ["name", "organization", "lead_name", "status"], as_dict=True
			)
		)
	if doctype == "CRM Lead" and name:
		return _lead(
			frappe.db.get_value("CRM Lead", name, ["name", "lead_name", "organization"], as_dict=True)
		)
	return {"link": "/crm/tasks"}


def _deal(d) -> dict[str, Any]:
	if not d:
		return {}
	return {
		"deal": d.organization or d.lead_name or d.name,
		"stage": d.get("status"),
		"link": f"/crm/deals/{d.name}",
	}


def _lead(lead) -> dict[str, Any]:
	if not lead:
		return {}
	return {
		"lead": lead.lead_name or lead.name,
		"company": lead.organization,
		"link": f"/crm/leads/{lead.name}",
	}
