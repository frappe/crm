# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import json
from dataclasses import dataclass

import frappe
from frappe import _

from crm.fcrm.doctype.crm_dashboard.home_columns import WidgetColumns
from crm.fcrm.doctype.crm_dashboard.home_widgets import DOCTYPES, TASK_DOCTYPES

HOME_PREFIX = "Home - "
MANAGER_ROLES = ("Sales Manager", "System Manager")
GRID_COLUMNS = 20


@dataclass(frozen=True)
class Widget:
	manager_only: bool = False
	doctype_setting: bool = True
	min_w: int = 1
	tasks: bool = False
	# Default column keys, in order; `locked` ones identify the widget and cannot be removed.
	columns: tuple = ()
	locked: tuple = ()

	def doctypes(self, setting: str) -> tuple:
		return TASK_DOCTYPES if self.tasks else DOCTYPES[setting]


REPLY_COLUMNS = ("title", "status", "channel", "awaiting_reply_since")
FOLLOW_UP_COLUMNS = ("title", "reference_title", "due_date")

# Task widgets need the full width for their title, record and assignee.
WIDGETS = {
	"replies_waiting": Widget(columns=REPLY_COLUMNS, locked=("title", "awaiting_reply_since")),
	"follow_ups_due": Widget(
		min_w=GRID_COLUMNS,
		tasks=True,
		columns=(*FOLLOW_UP_COLUMNS, "actions"),
		locked=("title", "due_date", "actions"),
	),
	"upcoming_follow_ups": Widget(
		min_w=GRID_COLUMNS, tasks=True, columns=FOLLOW_UP_COLUMNS, locked=("title", "due_date")
	),
	"assigned_to_me": Widget(columns=("title", "status", "assigned_at"), locked=("title", "assigned_at")),
	"recently_opened": Widget(columns=("title", "doctype", "status"), locked=("title",)),
	"no_next_step": Widget(
		columns=("title", "status", "idle_since", "follow_up"), locked=("title", "idle_since", "follow_up")
	),
	"my_tasks": Widget(
		doctype_setting=False,
		min_w=GRID_COLUMNS,
		tasks=True,
		columns=("status", "title", "priority", "due_date"),
		locked=("title", "due_date"),
	),
	"team_overview": Widget(manager_only=True, doctype_setting=False),
	"team_replies_waiting": Widget(
		manager_only=True, columns=(*REPLY_COLUMNS, "owner"), locked=("title", "awaiting_reply_since")
	),
	"team_overdue_follow_ups": Widget(
		manager_only=True,
		min_w=GRID_COLUMNS,
		tasks=True,
		columns=(*FOLLOW_UP_COLUMNS, "priority", "assigned_to"),
		locked=("title", "due_date", "assigned_to"),
	),
	"unassigned": Widget(
		manager_only=True, columns=("title", "status", "creation"), locked=("title", "creation")
	),
}


def role_for(user: str) -> str:
	if user == "Administrator" or set(MANAGER_ROLES) & set(frappe.get_roles(user)):
		return "manager"
	return "agent"


class HomeLayout:
	def __init__(self, user: str | None = None):
		self.user = user or frappe.session.user
		self.role = role_for(self.user)

	def get(self) -> dict:
		name = self._record()
		if not name:
			layout = RoleDefault(self.role).get_layout(self.user)
			return {"layout": layout, "is_default": True, "role": self.role}
		layout = load(frappe.db.get_value("CRM Dashboard", name, "layout"))
		return {"layout": allowed_items(layout, self.role, self.user), "is_default": False, "role": self.role}

	def save(self, layout) -> dict:
		layout = validate_layout(layout, self.role, self.user)
		name = self._record()
		if name:
			frappe.db.set_value("CRM Dashboard", name, "layout", json.dumps(layout))
		else:
			frappe.get_doc(
				{
					"doctype": "CRM Dashboard",
					"title": HOME_PREFIX + self.user,
					"private": 1,
					"user": self.user,
					"layout": json.dumps(layout),
				}
			).insert(ignore_permissions=True)
		return self.get()

	def reset(self) -> dict:
		if name := self._record():
			frappe.delete_doc("CRM Dashboard", name, ignore_permissions=True)
		return self.get()

	def _record(self) -> str | None:
		return frappe.db.get_value("CRM Dashboard", {"user": self.user, "name": ["like", HOME_PREFIX + "%"]})


class RoleDefault:
	def __init__(self, role: str):
		if role not in BUILT_IN_DEFAULTS:
			frappe.throw(_("Unknown role {0}").format(role))
		self.role = role
		self.name = f"{HOME_PREFIX}{role.title()} Default"

	def get(self) -> dict:
		return {
			"layout": self.get_layout(),
			"is_default": not frappe.db.exists("CRM Dashboard", self.name),
			"role": self.role,
		}

	def get_layout(self, user: str | None = None) -> list:
		"""Columns the viewing `user` cannot read are dropped."""
		layout = frappe.db.get_value("CRM Dashboard", self.name, "layout")
		return allowed_items(load(layout), self.role, user) if layout else BUILT_IN_DEFAULTS[self.role]()

	def save(self, layout) -> dict:
		layout = json.dumps(validate_layout(layout, self.role))
		if frappe.db.exists("CRM Dashboard", self.name):
			frappe.db.set_value("CRM Dashboard", self.name, "layout", layout)
		else:
			frappe.get_doc({"doctype": "CRM Dashboard", "title": self.name, "layout": layout}).insert(
				ignore_permissions=True
			)
		return self.get()

	def reset(self) -> dict:
		if frappe.db.exists("CRM Dashboard", self.name):
			frappe.delete_doc("CRM Dashboard", self.name, ignore_permissions=True)
		return self.get()


def validate_layout(layout, role: str, user: str | None = None) -> list:
	layout = load(layout) if isinstance(layout, str) else layout
	if not isinstance(layout, list):
		frappe.throw(_("Home layout must be a list of widgets"))

	seen = set()
	items = []
	for item in layout:
		name = item.get("name") if isinstance(item, dict) else None
		if name not in WIDGETS:
			frappe.throw(_("Unknown Home widget {0}").format(name))
		if name in seen:
			frappe.throw(_("Home widget {0} is added twice").format(name))
		if WIDGETS[name].manager_only and role != "manager":
			frappe.throw(_("Home widget {0} is only available to managers").format(name))
		seen.add(name)
		items.append(
			{"name": name, "config": _config(name, item.get("config"), user), "layout": _position(item)}
		)
	return items


def allowed_items(layout: list, role: str, user: str | None = None) -> list:
	return [
		_allowed_columns(_widen(item), user)
		for item in layout
		if item.get("name") in WIDGETS and (role == "manager" or not WIDGETS[item["name"]].manager_only)
	]


# Field permissions can change after a layout is saved, and role defaults are saved by someone else.
def _allowed_columns(item: dict, user: str | None) -> dict:
	config = item.get("config") or {}
	if "columns" not in config:
		return item
	config = {k: v for k, v in config.items() if k != "columns"}
	columns = widget_columns(item["name"], config, user).allowed(item["config"]["columns"])
	if columns is not None:
		config["columns"] = columns
	return {**item, "config": config}


def widget_columns(name: str, config: dict, user: str | None = None) -> WidgetColumns:
	spec = WIDGETS[name]
	return WidgetColumns(name, spec, spec.doctypes(config.get("doctype", "Both")), user)


# Layouts saved before a widget had a minimum width still render, at that width.
def _widen(item: dict) -> dict:
	min_w = WIDGETS[item["name"]].min_w
	layout = item.get("layout") or {}
	if layout.get("w", min_w) >= min_w:
		return item
	return {**item, "layout": {**layout, "x": 0, "w": min_w}}


def load(layout: str | None) -> list:
	try:
		return json.loads(layout or "[]")
	except ValueError:
		frappe.throw(_("Home layout is not valid JSON"))


def _config(name: str, config, user: str | None) -> dict:
	spec = WIDGETS[name]
	config = config or {}
	if not isinstance(config, dict) or set(config) - {"doctype", "columns"}:
		frappe.throw(_("Home widget {0} has invalid settings").format(name))
	if "doctype" in config and not spec.doctype_setting:
		frappe.throw(_("Home widget {0} has no doctype setting").format(name))

	clean = {}
	if spec.doctype_setting:
		clean["doctype"] = config.get("doctype", "Both")
		if clean["doctype"] not in DOCTYPES:
			frappe.throw(_("Home widget {0} can only be set to Lead, Deal or Both").format(name))
	if "columns" in config:
		clean["columns"] = widget_columns(name, clean, user).validate(config["columns"])
	return clean


def _position(item: dict) -> dict:
	layout = item.get("layout")
	keys = ("x", "y", "w", "h")
	valid = (
		isinstance(layout, dict)
		and all(isinstance(layout.get(k), int) and layout[k] >= 0 for k in keys)
		and layout["w"] >= 1
		and layout["h"] >= 1
		and layout["x"] + layout["w"] <= GRID_COLUMNS
	)
	if not valid:
		frappe.throw(_("Home widget {0} has an invalid position").format(item["name"]))
	if layout["w"] < WIDGETS[item["name"]].min_w:
		frappe.throw(_("Home widget {0} must span the full width").format(item["name"]))
	return {**{k: layout[k] for k in keys}, "i": item["name"]}


# Heights fit the content; see widgets.js for the arithmetic.
def _item(name: str, x: int, y: int, w: int = 10, h: int = 9) -> dict:
	config = {"doctype": "Both"} if WIDGETS[name].doctype_setting else {}
	return {"name": name, "config": config, "layout": {"x": x, "y": y, "w": w, "h": h, "i": name}}


def agent_default() -> list:
	return [
		_item("follow_ups_due", 0, 0, w=20),
		_item("replies_waiting", 0, 9),
		_item("assigned_to_me", 10, 9),
		_item("upcoming_follow_ups", 0, 18, w=20),
		_item("recently_opened", 0, 27),
		_item("no_next_step", 10, 27),
		_item("my_tasks", 0, 36, w=20),
	]


def manager_default() -> list:
	return [
		_item("team_overview", 0, 0),
		_item("unassigned", 10, 0),
		_item("team_overdue_follow_ups", 0, 9, w=20),
		_item("team_replies_waiting", 0, 18, w=20),
		_item("replies_waiting", 0, 27),
		_item("recently_opened", 10, 27),
	]


BUILT_IN_DEFAULTS = {"agent": agent_default, "manager": manager_default}
