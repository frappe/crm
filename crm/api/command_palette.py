import frappe
from frappe.utils import add_days, add_to_date, now_datetime

UPCOMING_LIMIT = 5
UPCOMING_TASK_DAYS = 7
UPCOMING_SLA_HOURS = 24
# Anything older than this is backlog, not something to surface as upcoming.
OVERDUE_GRACE_DAYS = 3
SLA_DUE_STATUSES = ["First Response Due", "Rolling Response Due"]
OPEN_TASK_STATUSES = ["Done", "Canceled"]

SEARCH_TYPES = {
	"CRM Lead": ("Lead", "lead_name", ["lead_name", "organization", "email", "mobile_no"]),
	"CRM Deal": ("Deal", "organization", ["organization", "email", "mobile_no"]),
	"Contact": ("Contact", "full_name", ["full_name", "email_id", "mobile_no"]),
	"CRM Organization": ("Organization", "organization_name", ["organization_name", "website"]),
}


@frappe.whitelist()
def search(query: str = "", recent_names: str | None = None):
	"""Return permission-filtered CRM records for the command palette."""
	query = (query or "").strip()
	recent = _parse_recent(recent_names)
	return {
		"matches": _search_all(query) if len(query) >= 2 else [],
		"recent": _get_recent(recent) if not query else [],
		"upcoming": _get_upcoming() if not query else [],
	}


def _get_upcoming():
	"""Tasks due soon and SLA response deadlines, nearest first."""
	items = _upcoming_tasks() + _upcoming_slas()
	items.sort(key=lambda item: item["due"])
	return items[:UPCOMING_LIMIT]


def _upcoming_tasks():
	if not frappe.has_permission("CRM Task", "read"):
		return []
	rows = frappe.get_list(
		"CRM Task",
		fields=["name", "title", "due_date", "reference_doctype", "reference_docname"],
		filters={
			"status": ["not in", OPEN_TASK_STATUSES],
			"assigned_to": frappe.session.user,
			"due_date": ["between", _window(UPCOMING_TASK_DAYS * 24)],
		},
		order_by="due_date asc",
		limit_page_length=UPCOMING_LIMIT,
	)
	return [_upcoming_task(row) for row in rows]


def _upcoming_task(row):
	reference = SEARCH_TYPES.get(row.reference_doctype)
	return {
		"kind": "task",
		"name": row.name,
		"title": row.title,
		"label": "Task",
		"due": str(row.due_date),
		"route": reference[0] if reference and row.reference_docname else "Tasks",
		"route_name": row.reference_docname if reference else None,
	}


def _window(hours):
	now = now_datetime()
	return [add_days(now, -OVERDUE_GRACE_DAYS), add_to_date(now, hours=hours)]


def _upcoming_slas():
	items = []
	for doctype, (route, title_field, _fields) in SEARCH_TYPES.items():
		if doctype not in ("CRM Lead", "CRM Deal") or not frappe.has_permission(doctype, "read"):
			continue
		items.extend(_upcoming_sla(doctype, route, title_field))
	return items


def _upcoming_sla(doctype, route, title_field):
	rows = frappe.get_list(
		doctype,
		fields=["name", title_field, "response_by"],
		filters={
			"sla_status": ["in", SLA_DUE_STATUSES],
			"response_by": ["between", _window(UPCOMING_SLA_HOURS)],
			"_assign": ["like", f"%{frappe.session.user}%"],
		},
		order_by="response_by asc",
		limit_page_length=UPCOMING_LIMIT,
	)
	return [
		{
			"kind": "sla",
			"name": row.name,
			"title": row.get(title_field) or row.name,
			"label": "Response due",
			"due": str(row.response_by),
			"route": route,
			"route_name": row.name,
		}
		for row in rows
	]


def _parse_recent(value: str | None):
	try:
		recent = frappe.parse_json(value or "{}")
	except (TypeError, ValueError):
		return {}
	return recent if isinstance(recent, dict) else {}


def _search_all(query: str):
	results = []
	for doctype, config in SEARCH_TYPES.items():
		if frappe.has_permission(doctype, "read"):
			results.extend(_search_doctype(doctype, config, query))
	return results


def _search_doctype(doctype: str, config: tuple, query: str):
	route, title_field, search_fields = config
	fields = ["name", title_field, *search_fields]
	rows = frappe.get_list(
		doctype,
		fields=list(dict.fromkeys(fields)),
		or_filters=[[field, "like", f"%{query}%"] for field in ["name", *search_fields]],
		order_by="modified desc",
		limit_page_length=5,
	)
	return [
		{**_record(row, doctype, route, title_field), "keywords": _keywords(row, search_fields)}
		for row in rows
	]


def _keywords(row, search_fields: list[str]):
	"""Non-title matched values, so the client can rank title hits above them."""
	return " ".join(str(row.get(field)) for field in ["name", *search_fields] if row.get(field))


def _get_recent(recent: dict):
	results = []
	for doctype, names in recent.items():
		if doctype in SEARCH_TYPES and isinstance(names, list) and frappe.has_permission(doctype, "read"):
			results.extend(_recent_doctype(doctype, names[:5]))
	return results


def _recent_doctype(doctype: str, names: list[str]):
	if not names:
		return []
	route, title_field, _search_fields = SEARCH_TYPES[doctype]
	rows = frappe.get_list(doctype, fields=["name", title_field], filters={"name": ["in", names]})
	by_name = {row.name: row for row in rows}
	return [_record(by_name[name], doctype, route, title_field) for name in names if name in by_name]


def _record(row, doctype: str, route: str, title_field: str):
	return {
		"doctype": doctype,
		"name": row.name,
		"title": row.get(title_field) or row.name,
		"route": route,
	}
