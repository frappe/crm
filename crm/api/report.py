import json

import frappe
from frappe import _
from frappe.utils import cint, flt

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


def _get_report_error(report_name: str) -> tuple[type[Exception], str] | None:
	"""Why a report can't be used in CRM, as (exception class, message), or None if it can."""
	if not report_name or not frappe.db.exists("Report", report_name):
		return frappe.DoesNotExistError, _("Report {0} not found").format(report_name)

	report = frappe.get_doc("Report", report_name)
	if report.module != "FCRM":
		return frappe.PermissionError, _("Only reports under the FCRM module are available in CRM.")
	if report.disabled:
		return frappe.ValidationError, _("Report {0} is disabled.").format(report_name)
	if report.report_type == "Report Builder":
		return frappe.ValidationError, _("Report Builder reports are not supported in CRM.")
	if report.prepared_report:
		return frappe.ValidationError, _("Prepared Reports are not supported in CRM.")
	if not _is_report_permitted(report):
		return frappe.PermissionError, _("You don't have access to Report: {0}").format(report_name)
	return None


def _is_report_permitted(report) -> bool:
	"""The access check core runs before a report (get_report_doc), without throwing.

	Like core, a Custom Report is checked against the report it is based on.
	"""
	from frappe.desk.query_report import get_reference_report

	report = get_reference_report(report)
	if not report.is_permitted():
		return False
	return not report.ref_doctype or frappe.has_permission(report.ref_doctype, "report")


def _validate_fcrm_report(report_name: str):
	"""Throw unless the report is an FCRM report the current user can run."""
	if error := _get_report_error(report_name):
		exc, message = error
		frappe.throw(message, exc)
	return frappe.get_doc("Report", report_name)


def _get_user_pinned_list(user: str | None = None) -> list[dict]:
	"""Retrieve the current user's pinned reports from user defaults."""
	raw = frappe.defaults.get_user_default(PINNED_REPORTS_KEY, user=user or frappe.session.user)
	if not raw:
		return []
	try:
		data = json.loads(raw) if isinstance(raw, str) else raw
	except Exception:
		return []
	if not isinstance(data, list):
		return []
	return [row for row in data if isinstance(row, dict) and row.get("report")]


def _set_user_pinned_list(reports: list[dict], user: str | None = None):
	"""Persist the current user's pinned reports to user defaults."""
	frappe.defaults.set_user_default(
		PINNED_REPORTS_KEY, json.dumps(reports), user=user or frappe.session.user
	)


SUPPORTED_REPORT_FILTERS = {
	"module": "FCRM",
	"disabled": 0,
	"report_type": ["in", ["Query Report", "Script Report", "Custom Report"]],
	"prepared_report": 0,
}


@frappe.whitelist()
@sales_user_only
def get_fcrm_reports():
	"""FCRM reports the current user can run, for the Settings > Reports picker.

	Uses the same access check as pinning, so everything listed here can be pinned.
	Report Builder and Prepared Reports are not supported by the CRM report page.
	"""
	reports = frappe.get_all(
		"Report",
		filters=SUPPORTED_REPORT_FILTERS,
		fields=["name", "report_name", "report_type"],
		order_by="report_name asc",
	)
	pinned = {row["report"] for row in _get_user_pinned_list()}

	return [
		{
			"name": report.name,
			"title": report.report_name or report.name,
			"report_type": report.report_type or "Report",
			"pinned": report.name in pinned,
		}
		for report in reports
		if _is_report_permitted(frappe.get_doc("Report", report.name))
	]


@frappe.whitelist()
@sales_user_only
def get_pinned_reports():
	"""The current user's pinned reports, for the CRM UI sidebar."""
	pinned = _get_user_pinned_list()
	if not pinned:
		return []

	reports = {
		r.name: r
		for r in frappe.get_all(
			"Report",
			filters={"name": ["in", [row["report"] for row in pinned]], **SUPPORTED_REPORT_FILTERS},
			fields=["name", "report_name"],
		)
	}

	return [
		{
			"report": row["report"],
			# always the current name, so renaming the report updates the sidebar
			"title": reports[row["report"]].report_name or row["report"],
			"icon": row.get("icon"),
		}
		for row in pinned
		if row["report"] in reports and _is_report_permitted(frappe.get_doc("Report", row["report"]))
	]


@frappe.whitelist()
@sales_user_only
def pin_report(report: str, icon: str | None = None):
	_validate_fcrm_report(report)

	pinned = _get_user_pinned_list()
	if any(row["report"] == report for row in pinned):
		return

	pinned.append({"report": report, "icon": icon})
	_set_user_pinned_list(pinned)


@frappe.whitelist()
@sales_user_only
def pin_reports(reports: str | list):
	"""Pin several reports at once.

	Reports that can't be pinned are skipped, not fatal, and returned with the
	reason so the UI can tell the user.
	"""
	if isinstance(reports, str):
		reports = frappe.parse_json(reports)

	pinned = _get_user_pinned_list()
	existing = {row["report"] for row in pinned}
	added, skipped = [], []

	for item in reports or []:
		report_name = item if isinstance(item, str) else item.get("report")
		if not report_name or report_name in existing:
			continue
		if error := _get_report_error(report_name):
			skipped.append({"report": report_name, "reason": error[1]})
			continue

		pinned.append({"report": report_name, "icon": None if isinstance(item, str) else item.get("icon")})
		existing.add(report_name)
		added.append(report_name)

	if added:
		_set_user_pinned_list(pinned)
	return {"added": added, "skipped": skipped}


@frappe.whitelist()
@sales_user_only
def unpin_report(report: str):
	pinned = _get_user_pinned_list()
	_set_user_pinned_list([row for row in pinned if row["report"] != report])


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

	# run() already turns columns and rows into dicts. If user supplied non-empty filters,
	# pass are_default_filters=False so they aren't overwritten by a Custom Report's saved
	# filters; with no filters, pass True so the saved filters apply.
	res = run(report_name, filters=filters, are_default_filters=not _has_values(filters))

	columns = [_normalize_column(col) for col in res.get("columns") or []]
	rows = res.get("result") or []

	# add_total_row appends a plain list ("Total", sums...) after the dict rows;
	# return it separately so it is never shown or linked like a record
	total_row = None
	if res.get("add_total_row") and rows and isinstance(rows[-1], list | tuple):
		total_row = dict(zip([c["key"] for c in columns], rows.pop(), strict=False))

	return {
		"columns": columns,
		"rows": rows,
		"total_row": total_row,
		"default_currency": frappe.db.get_default("currency"),
		"message": res.get("message"),
		"chart": res.get("chart"),
		"report_summary": res.get("report_summary"),
	}


def _has_values(filters) -> bool:
	return isinstance(filters, dict) and any(v not in (None, "", []) for v in filters.values())


def _normalize_column(col: dict) -> dict:
	col_type = col.get("fieldtype") or "Data"
	return {
		"key": col.get("fieldname"),
		"label": col.get("label") or col.get("fieldname"),
		"type": col_type,
		"options": col.get("options"),
		"width": _css_width(col.get("width")),
		"align": col.get("align") or ("right" if col_type in NUMERIC_COLUMN_TYPES else "left"),
		# kept so the table and export can drop hidden columns themselves
		"hidden": col.get("hidden", 0),
	}


NUMERIC_COLUMN_TYPES = ("Currency", "Float", "Int", "Percent")


def _css_width(width) -> str:
	"""Report widths are pixels, given as numbers or numeric strings ("120")."""
	if width in (None, ""):
		return "150px"
	if isinstance(width, int | float) or str(width).strip().replace(".", "", 1).isdigit():
		return f"{cint(flt(width))}px"
	return str(width)


@frappe.whitelist()
@sales_user_only
def export_report(
	report_name: str,
	file_format_type: str = "Excel",
	filters: str | dict | None = None,
	custom_columns: str | list | None = None,
	visible_columns: str | list | None = None,
	applied_filters: str | dict | None = None,
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
	if isinstance(applied_filters, str):
		applied_filters = frappe.parse_json(applied_filters)

	ref_doctype = frappe.get_cached_value("Report", report_name, "ref_doctype")
	if ref_doctype:
		frappe.permissions.can_export(ref_doctype, raise_exception=True)

	res = run(
		report_name,
		filters=filters or {},
		custom_columns=custom_columns or [],
		are_default_filters=not _has_values(filters),
	)

	data = frappe._dict(res)
	data.report_name = report_name
	data.filters = filters or {}
	# build_xlsx_data prints applied_filters in the "Include filters" header.
	# Like desk, the client sends them keyed by label with display values.
	data.applied_filters = applied_filters or filters or {}

	if not data.columns:
		# a real error, not an HTML page: the client would save that as the file
		frappe.throw(
			_("No data to export. You can try changing the filters of your report."),
			frappe.ValidationError,
			title=_("No data to export"),
		)

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
