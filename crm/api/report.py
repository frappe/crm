import json

import frappe
from frappe import _

from crm.utils import sales_user_only

# --- "Add an existing report to the CRM sidebar" feature ---------------------
#
# Any Report (Query Report / Script Report) that lives under this app's
# "FCRM" module is presumed built for CRM data and safe to offer.
# Each CRM user picks which of those they want from Settings > Reports.
# Selection is saved to user defaults via standard tabDefaultValue so no
# extra custom doctype or migration is required.
# Reports are loaded within /crm/reports/<name>.

PINNED_REPORTS_KEY = "_crm_pinned_reports"


def _validate_fcrm_report(report_name: str):
	"""Validate that the report exists, belongs to the FCRM module, and is accessible to the current user."""
	if not frappe.db.exists("Report", report_name):
		frappe.throw(_("Report {0} not found").format(report_name), frappe.DoesNotExistError)

	report = frappe.get_doc("Report", report_name)
	if report.module != "FCRM":
		frappe.throw(
			_("Only reports under the FCRM module are available in CRM."),
			frappe.PermissionError,
		)
	if getattr(report, "disabled", 0):
		frappe.throw(
			_("Report {0} is disabled.").format(report_name),
			frappe.ValidationError,
		)
	if report.report_type == "Report Builder":
		frappe.throw(
			_("Report Builder reports are not supported in CRM."),
			frappe.ValidationError,
		)
	if getattr(report, "prepared_report", 0):
		frappe.throw(
			_("Prepared Reports are not supported in CRM."),
			frappe.ValidationError,
		)
	if report.ref_doctype and not frappe.has_permission(report.ref_doctype, "report"):
		frappe.throw(
			_("You don't have report permission for: {0}").format(report.ref_doctype),
			frappe.PermissionError,
		)
	if not report.is_permitted():
		frappe.throw(
			_("You don't have access to Report: {0}").format(report_name),
			frappe.PermissionError,
		)
	return report


def _get_user_pinned_list(user: str | None = None) -> list[dict]:
	"""Retrieve the current user's pinned reports from user defaults."""
	raw = frappe.defaults.get_user_default(PINNED_REPORTS_KEY, user=user or frappe.session.user)
	if not raw:
		return []
	try:
		data = json.loads(raw) if isinstance(raw, str) else raw
		return data if isinstance(data, list) else []
	except Exception:
		return []


def _set_user_pinned_list(reports: list[dict], user: str | None = None):
	"""Persist the current user's pinned reports to user defaults."""
	frappe.defaults.set_user_default(
		PINNED_REPORTS_KEY, json.dumps(reports), user=user or frappe.session.user
	)


@frappe.whitelist()
@sales_user_only
def get_fcrm_reports():
	"""Permitted interactive reports under the FCRM module for the Settings > Reports picker.

	Explicitly excludes:
	- Report Builder reports (require desk report view, not supported in standalone runner)
	- Prepared Reports (run as async background jobs, not supported in interactive viewer)
	"""
	reports = frappe.get_all(
		"Report",
		filters={
			"module": "FCRM",
			"disabled": 0,
			"report_type": ["in", ["Query Report", "Script Report", "Custom Report"]],
			"prepared_report": 0,
		},
		fields=["name", "report_name", "report_type"],
		order_by="report_name asc",
	)

	report_names = [r["name"] for r in reports]
	permitted_names = _filter_permitted_reports(report_names)

	pinned = {
		item["report"] for item in _get_user_pinned_list() if isinstance(item, dict) and "report" in item
	}

	return [
		{
			"name": report["name"],
			"title": report.get("report_name") or report["name"],
			"report_type": report.get("report_type") or "Report",
			"pinned": report["name"] in pinned,
		}
		for report in reports
		if report["name"] in permitted_names
	]


def _filter_permitted_reports(report_names: list[str]) -> set[str]:
	"""Filter report names by checking role and ref_doctype permissions in batch."""
	if not report_names:
		return set()

	user_roles = set(frappe.get_roles())
	is_admin = "System Manager" in user_roles or frappe.session.user == "Administrator"

	# 1. Fetch custom roles for any of these reports in a single query
	custom_role_records = frappe.get_all(
		"Custom Role",
		filters={"report": ["in", report_names]},
		fields=["name", "report"],
	)
	custom_role_map = {}
	if custom_role_records:
		custom_role_names = [cr["name"] for cr in custom_role_records]
		cr_roles = frappe.get_all(
			"Has Role",
			filters={"parent": ["in", custom_role_names], "parenttype": "Custom Role"},
			fields=["parent", "role"],
		)
		cr_to_roles = {}
		for row in cr_roles:
			cr_to_roles.setdefault(row["parent"], set()).add(row["role"])
		for cr in custom_role_records:
			custom_role_map[cr["report"]] = cr_to_roles.get(cr["name"], set())

	# 2. Fetch standard roles from Has Role child table for Report in a single query
	standard_roles = frappe.get_all(
		"Has Role",
		filters={"parent": ["in", report_names], "parenttype": "Report"},
		fields=["parent", "role"],
	)
	report_to_std_roles = {}
	for row in standard_roles:
		report_to_std_roles.setdefault(row["parent"], set()).add(row["role"])

	role_permitted = set()
	for name in report_names:
		if is_admin:
			role_permitted.add(name)
			continue

		allowed = report_to_std_roles.get(name, set())
		custom_roles = custom_role_map.get(name)
		if custom_roles:
			allowed = custom_roles

		# If no specific roles required, or user has at least one allowed role
		if not allowed or bool(user_roles & allowed):
			role_permitted.add(name)

	if not role_permitted:
		return set()

	# 3. Filter by ref_doctype report permission
	report_docs = frappe.get_all(
		"Report",
		filters={"name": ["in", list(role_permitted)]},
		fields=["name", "ref_doctype"],
	)
	final_permitted = set()
	for r in report_docs:
		ref_doctype = r.get("ref_doctype")
		if not ref_doctype or frappe.has_permission(ref_doctype, "report"):
			final_permitted.add(r["name"])

	return final_permitted


@frappe.whitelist()
@sales_user_only
def get_pinned_reports():
	"""The current user's pinned reports, for the CRM UI sidebar."""
	pinned = _get_user_pinned_list()
	if not pinned:
		return []

	report_names = [
		row.get("report") or row.get("name")
		for row in pinned
		if isinstance(row, dict) and (row.get("report") or row.get("name"))
	]
	if not report_names:
		return []

	fcrm_reports = {
		r.name: r
		for r in frappe.get_all(
			"Report",
			filters={
				"name": ["in", report_names],
				"module": "FCRM",
				"disabled": 0,
				"report_type": ["in", ["Query Report", "Script Report", "Custom Report"]],
				"prepared_report": 0,
			},
			fields=["name", "report_name"],
		)
	}
	if not fcrm_reports:
		return []

	permitted_names = _filter_permitted_reports(list(fcrm_reports.keys()))

	result = []
	for row in pinned:
		if not isinstance(row, dict):
			continue
		report_name = row.get("report") or row.get("name")
		if not report_name or report_name not in fcrm_reports or report_name not in permitted_names:
			continue
		result.append(
			{
				"name": report_name,
				"report": report_name,
				"title": row.get("title") or fcrm_reports[report_name].report_name or report_name,
				"icon": row.get("icon"),
			}
		)
	return result


@frappe.whitelist()
@sales_user_only
def pin_report(report: str, title: str | None = None, icon: str | None = None):
	report_doc = _validate_fcrm_report(report)

	pinned = _get_user_pinned_list()
	for row in pinned:
		if isinstance(row, dict) and (row.get("report") == report or row.get("name") == report):
			return

	pinned.append(
		{
			"name": report,
			"report": report,
			"title": title or report_doc.report_name or report,
			"icon": icon,
		}
	)
	_set_user_pinned_list(pinned)


@frappe.whitelist()
@sales_user_only
def pin_reports(reports: str | list):
	"""Pins multiple reports at once, preventing duplicates and validating in batch."""
	if isinstance(reports, str):
		reports = frappe.parse_json(reports)

	if not reports:
		return

	pinned = _get_user_pinned_list()
	existing_keys = {row.get("report") or row.get("name") for row in pinned if isinstance(row, dict)}

	for item in reports:
		report_name = item if isinstance(item, str) else item.get("report") or item.get("name")
		if not report_name or report_name in existing_keys:
			continue
		try:
			report_doc = _validate_fcrm_report(report_name)
		except (frappe.PermissionError, frappe.DoesNotExistError, frappe.ValidationError):
			# Skip invalid or inaccessible reports instead of aborting
			# the whole batch — other valid selections should still be saved.
			continue
		title = (
			(None if isinstance(item, str) else item.get("title")) or report_doc.report_name or report_name
		)
		icon = None if isinstance(item, str) else item.get("icon")
		pinned.append(
			{
				"name": report_name,
				"report": report_name,
				"title": title,
				"icon": icon,
			}
		)
		existing_keys.add(report_name)

	_set_user_pinned_list(pinned)


@frappe.whitelist()
@sales_user_only
def unpin_report(report: str):
	pinned = _get_user_pinned_list()
	new_pinned = [
		row
		for row in pinned
		if isinstance(row, dict) and row.get("report") != report and row.get("name") != report
	]
	_set_user_pinned_list(new_pinned)


@frappe.whitelist()
@sales_user_only
def get_report_meta(report_name: str):
	"""Returns the metadata, ref_doctype, and filter definitions for a report."""
	report_doc = _validate_fcrm_report(report_name)

	from frappe.desk.query_report import get_script

	script_data = get_script(report_name)

	filters = script_data.get("filters") or []
	if not filters and report_doc.json:
		try:
			data = frappe.parse_json(report_doc.json)
			filters = data.get("filters", [])
		except Exception:
			pass

	return {
		"name": report_doc.name,
		"report_name": report_doc.report_name,
		"ref_doctype": report_doc.ref_doctype,
		"report_type": report_doc.report_type,
		"script": script_data.get("script"),
		"filters": filters,
	}


@frappe.whitelist()
@sales_user_only
def get_report_data(
	report_name: str,
	filters: str | dict | None = None,
):
	"""Runs any report and returns structured columns and rows for the CRM standalone UI."""
	_validate_fcrm_report(report_name)

	if isinstance(filters, str):
		filters = frappe.parse_json(filters)

	from frappe.desk.query_report import run

	# If user supplied non-empty filters, pass are_default_filters=False so they aren't
	# overwritten by the report's custom_filters. If no filters were provided, pass
	# are_default_filters=True so a Custom Report's saved filters can be applied.
	has_filters = isinstance(filters, dict) and any(v is not None and v != "" for v in filters.values())
	res = run(report_name, filters=filters, are_default_filters=not has_filters)
	raw_columns = res.get("columns", [])
	raw_result = res.get("result", [])

	normalized_columns = []
	for col in raw_columns:
		if isinstance(col, str):
			parts = col.split(":")
			label = parts[0]
			col_type = "Data"
			options = None
			width = "150px"
			if len(parts) > 1:
				type_parts = parts[1].split("/")
				col_type = type_parts[0]
				if len(type_parts) > 1:
					options = type_parts[1]
			if len(parts) > 2:
				width = f"{parts[2]}px"
			fieldname = frappe.scrub(label)
			normalized_columns.append(
				{
					"key": fieldname,
					"label": label,
					"type": col_type,
					"options": options,
					"width": width,
					"align": "right" if col_type in ("Currency", "Float", "Int", "Percent") else "left",
					"hidden": 0,
				}
			)
		elif isinstance(col, dict):
			fieldname = col.get("fieldname") or frappe.scrub(col.get("label", ""))
			col_type = col.get("fieldtype") or "Data"
			width = col.get("width")
			width_str = f"{width}px" if isinstance(width, int | float) else (width or "150px")
			# Preserve the hidden flag on the column object to keep normalized_columns
			# matching 1-to-1 with raw row tuples, while allowing the table and export
			# to filter by col.hidden.
			normalized_columns.append(
				{
					"key": fieldname,
					"label": col.get("label") or fieldname,
					"type": col_type,
					"options": col.get("options"),
					"width": width_str,
					"align": col.get("align")
					or ("right" if col_type in ("Currency", "Float", "Int", "Percent") else "left"),
					"hidden": col.get("hidden", 0),
				}
			)

	normalized_rows = []
	column_keys = [c["key"] for c in normalized_columns]
	for row in raw_result:
		if isinstance(row, list | tuple):
			normalized_rows.append(dict(zip(column_keys, row, strict=False)))
		elif isinstance(row, dict):
			normalized_rows.append(row)

	return {
		"columns": normalized_columns,
		"rows": normalized_rows,
		"message": res.get("message"),
		"chart": res.get("chart"),
		"report_summary": res.get("report_summary"),
	}


@frappe.whitelist()
@sales_user_only
def export_report(
	report_name: str,
	file_format_type: str = "Excel",
	filters: str | dict | None = None,
	custom_columns: str | list | None = None,
	visible_columns: str | list | None = None,
	include_filters: int | bool = 1,
	include_hidden_columns: int | bool = 0,
	csv_delimiter: str = ",",
	csv_quoting: int = 2,
	csv_decimal_sep: str = ".",
):
	"""Export report data to Excel or CSV via Frappe Desk's query_report runner."""
	_validate_fcrm_report(report_name)

	from frappe.desk.query_report import build_xlsx_data, format_fields, run
	from frappe.desk.utils import get_csv_bytes, provide_binary_file
	from frappe.utils.xlsxutils import handle_html, make_xlsx

	if isinstance(filters, str):
		filters = frappe.parse_json(filters)
	if isinstance(custom_columns, str):
		custom_columns = frappe.parse_json(custom_columns)
	if isinstance(visible_columns, str):
		visible_columns = frappe.parse_json(visible_columns)

	ref_doctype = frappe.get_cached_value("Report", report_name, "ref_doctype")
	if ref_doctype:
		frappe.permissions.can_export(ref_doctype, raise_exception=True)

	has_filters = isinstance(filters, dict) and any(v is not None and v != "" for v in filters.values())
	res = run(
		report_name,
		filters=filters or {},
		custom_columns=custom_columns or [],
		are_default_filters=not has_filters,
	)

	data = frappe._dict(res)
	data.report_name = report_name
	data.filters = filters or {}
	# Frappe's build_xlsx_data reads applied_filters (not filters) when
	# rendering the "Include applied filters" header row.
	data.applied_filters = filters or {}

	if not data.columns:
		frappe.respond_as_web_page(
			_("No data to export"),
			_("You can try changing the filters of your report."),
		)
		return

	# If visible_columns is provided and user did not check include_hidden_columns,
	# mark unselected columns as hidden so build_xlsx_data excludes them.
	if visible_columns and not include_hidden_columns:
		visible_set = set(visible_columns)
		for col in data.columns:
			key = col.get("fieldname") or frappe.scrub(col.get("label", ""))
			if key not in visible_set and col.get("fieldname") not in visible_set:
				col["hidden"] = 1

	format_fields(data, file_format_type)

	xlsx_data, column_widths, styles = build_xlsx_data(
		data,
		include_indentation=0,
		include_filters=bool(include_filters),
		include_hidden_columns=bool(include_hidden_columns),
		build_styles=file_format_type == "Excel",
	)

	csv_params = {
		"delimiter": csv_delimiter or ",",
		"quoting": int(csv_quoting if csv_quoting is not None else 2),
		"decimal_sep": csv_decimal_sep or ".",
	}

	if file_format_type == "CSV":
		file_extension = "csv"
		content = get_csv_bytes(
			[[handle_html(v) if isinstance(v, str) else v for v in r] for r in xlsx_data],
			csv_params,
		)
	elif file_format_type == "Excel":
		file_extension = "xlsx"
		content = make_xlsx(
			xlsx_data,
			report_name,
			column_widths=column_widths,
			styles=styles,
		).getvalue()
	else:
		frappe.throw(
			title=_("Unsupported file format: {0}").format(file_format_type),
			msg=_("Only CSV and Excel formats are supported for export"),
		)

	provide_binary_file(_(report_name), file_extension, content)
