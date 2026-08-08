import frappe


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
	}


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
	return [_record(row, doctype, route, title_field) for row in rows]


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
