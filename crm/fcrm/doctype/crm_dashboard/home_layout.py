# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import json
from dataclasses import dataclass

import frappe
from frappe import _

HOME_PREFIX = "Home - "
MANAGER_ROLES = ("Sales Manager", "System Manager")
DOCTYPE_OPTIONS = ("Lead", "Deal", "Both")
# Rolling windows the sales cards compare against the window before them, as Helpdesk's cards do.
PERIOD_DAYS = {"last_week": 7, "last_month": 30, "last_3_months": 90}
DEFAULT_PERIOD = "last_month"
GRID_COLUMNS = 20
MAX_WIDGETS = 3


@dataclass(frozen=True)
class Widget:
	manager_only: bool = False
	doctype_setting: bool = True
	period_setting: bool = False
	min_w: int = 1
	min_h: int = 1


# My tasks leaves room beside it for two stacked cards.
WIDGETS = {
	"tasks": Widget(doctype_setting=False, min_w=12, min_h=8),
	"leads_and_deals": Widget(),
	"leads": Widget(doctype_setting=False),
	"deals": Widget(doctype_setting=False),
	"recently_opened": Widget(),
	"no_next_step": Widget(),
	"funnel_conversion": Widget(doctype_setting=False, period_setting=True),
	"won_this_month": Widget(doctype_setting=False, period_setting=True),
	"expected_revenue": Widget(doctype_setting=False, period_setting=True),
	"top_open_deals": Widget(doctype_setting=False),
	"team_overview": Widget(manager_only=True, doctype_setting=False, period_setting=True, min_h=10),
	"team_replies_waiting": Widget(manager_only=True),
	"overdue_and_unassigned": Widget(manager_only=True, doctype_setting=False),
}


def period_days(period: str) -> int:
	if period not in PERIOD_DAYS:
		frappe.throw(_("Unknown period {0}").format(period))
	return PERIOD_DAYS[period]


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
			return {"layout": RoleDefault(self.role).get_layout(), "is_default": True, "role": self.role}
		layout = load(frappe.db.get_value("CRM Dashboard", name, "layout"))
		return {"layout": allowed_items(layout, self.role), "is_default": False, "role": self.role}

	def save(self, layout) -> dict:
		layout = validate_layout(layout, self.role)
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

	def get_layout(self) -> list:
		layout = frappe.db.get_value("CRM Dashboard", self.name, "layout")
		return allowed_items(load(layout), self.role) if layout else BUILT_IN_DEFAULTS[self.role]()

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


def validate_layout(layout, role: str) -> list:
	layout = load(layout) if isinstance(layout, str) else layout
	if not isinstance(layout, list):
		frappe.throw(_("Home layout must be a list of widgets"))

	if len(layout) > MAX_WIDGETS:
		frappe.throw(_("Home can hold up to {0} widgets").format(MAX_WIDGETS))

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
		items.append({"name": name, "config": _config(name, item.get("config")), "layout": _position(item)})
	return items


def allowed_items(layout: list, role: str) -> list:
	allowed = [
		_fit_minimum(item)
		for item in layout
		if item.get("name") in WIDGETS and (role == "manager" or not WIDGETS[item["name"]].manager_only)
	]
	return allowed[:MAX_WIDGETS]


# Layouts saved before a widget had a minimum size still render, at that size.
def _fit_minimum(item: dict) -> dict:
	widget = WIDGETS[item["name"]]
	layout = item.get("layout") or {}
	if layout.get("w", widget.min_w) < widget.min_w:
		layout = {**layout, "x": 0, "w": widget.min_w}
	if layout.get("h", widget.min_h) < widget.min_h:
		layout = {**layout, "h": widget.min_h}
	return {**item, "layout": layout} if layout != item.get("layout") else item


def load(layout: str | None) -> list:
	try:
		return json.loads(layout or "[]")
	except ValueError:
		frappe.throw(_("Home layout is not valid JSON"))


def _config(name: str, config) -> dict:
	widget = WIDGETS[name]
	config = config or {}
	allowed = {"doctype"} if widget.doctype_setting else set()
	if widget.period_setting:
		allowed.add("period")
	if not isinstance(config, dict) or set(config) - allowed:
		frappe.throw(_("Home widget {0} has no such setting").format(name))

	settings = {}
	if widget.doctype_setting:
		settings["doctype"] = config.get("doctype", "Both")
		if settings["doctype"] not in DOCTYPE_OPTIONS:
			frappe.throw(_("Home widget {0} can only be set to Lead, Deal or Both").format(name))
	if "period" in config:
		if config["period"] not in PERIOD_DAYS:
			frappe.throw(_("Home widget {0} can only compare last week, month or 3 months").format(name))
		settings["period"] = config["period"]
	return settings


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
	widget = WIDGETS[item["name"]]
	if layout["w"] < widget.min_w or layout["h"] < widget.min_h:
		frappe.throw(_("Home widget {0} is smaller than its minimum size").format(item["name"]))
	return {**{k: layout[k] for k in keys}, "i": item["name"]}


# Heights fit the content; see widgets.js for the arithmetic.
def _item(
	name: str, x: int, y: int, w: int = 10, h: int = 10, doctype: str = "Both", period: str | None = None
) -> dict:
	config = {"doctype": doctype} if WIDGETS[name].doctype_setting else {}
	if period:
		config["period"] = period
	return {"name": name, "config": config, "layout": {"x": x, "y": y, "w": w, "h": h, "i": name}}


def agent_default() -> list:
	return [
		_item("tasks", 0, 0, w=15, h=8),
		_item("expected_revenue", 15, 0, w=5, h=4, period="last_3_months"),
		_item("won_this_month", 15, 4, w=5, h=4, period="last_3_months"),
	]


def manager_default() -> list:
	return [
		_item("team_overview", 0, 0, w=15, h=10),
		_item("won_this_month", 15, 0, w=5, h=5),
		_item("expected_revenue", 15, 5, w=5, h=5),
	]


BUILT_IN_DEFAULTS = {"agent": agent_default, "manager": manager_default}
