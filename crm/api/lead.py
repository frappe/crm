import datetime
import json

import frappe
from frappe import _
from frappe.model.dynamic_links import get_dynamic_link_map
from frappe.model.rename_doc import get_link_fields

from crm.integrations.api import find_by_phone
from crm.utils import normalize_phone


@frappe.whitelist()
def find_duplicate_leads(lead_name: str):
	if not frappe.has_permission("CRM Lead", "read", lead_name):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	lead = frappe.get_cached_doc("CRM Lead", lead_name)

	candidates = set()
	if lead.email:
		candidates.update(frappe.get_all("CRM Lead", filters={"email": lead.email}, pluck="name"))
	for number in (lead.mobile_no, lead.phone):
		if number:
			candidates.update(m["docname"] for m in find_by_phone(number) if m["doctype"] == "CRM Lead")
	candidates.discard(lead_name)
	if not candidates:
		return []

	possible = frappe.get_list(
		"CRM Lead",
		filters={"name": ("in", list(candidates)), "converted": 0, "is_duplicate": 0},
		fields=["name", "lead_name", "email", "mobile_no", "phone", "organization"],
		limit=20,
	)

	numbers = {normalize_phone(n) for n in (lead.mobile_no, lead.phone)} - {""}
	return [{**p, "matched_fields": _matched_fields(lead, p, numbers)} for p in possible]


def _matched_fields(lead, candidate, numbers: set) -> list:
	matched = []
	if lead.email and (candidate.email or "").lower() == lead.email.lower():
		matched.append("email")
	for field in ("mobile_no", "phone"):
		if normalize_phone(candidate.get(field)) in numbers:
			matched.append(field)
	return matched


@frappe.whitelist()
def search_mergeable_leads(txt: str = "", current_lead: str = "", limit: int = 20):
	user = frappe.session.user

	filters = [["is_duplicate", "=", 0]]
	if current_lead:
		filters.append(["name", "!=", current_lead])

	or_filters = [
		["_assign", "like", f"%{user}%"],
		["_assign", "is", "not set"],
	]

	candidates = frappe.get_list(
		"CRM Lead",
		filters=filters,
		or_filters=or_filters,
		fields=["name", "lead_name", "email", "organization"],
		order_by="modified desc",
		limit_page_length=max(int(limit) * 5, 50),
	)

	if txt:
		needle = txt.lower()
		candidates = [
			r
			for r in candidates
			if any(
				(r.get(f) or "").lower().find(needle) != -1
				for f in ("name", "lead_name", "email", "organization")
			)
		]

	return [
		{
			"value": r["name"],
			"label": r.get("lead_name") or r["name"],
			"description": r.get("email") or r.get("organization") or "",
		}
		for r in candidates[: int(limit)]
	]


@frappe.whitelist()
def merge_leads(target: str, source: str):
	target_doc = frappe.get_doc("CRM Lead", target)
	source_doc = frappe.get_doc("CRM Lead", source)

	if not frappe.has_permission("CRM Lead", "write", target):
		frappe.throw(_("Not allowed to modify target lead"), frappe.PermissionError)
	if not frappe.has_permission("CRM Lead", "write", source):
		frappe.throw(_("Not allowed to modify source lead"), frappe.PermissionError)

	if source_doc.merged_into:
		frappe.throw(_("Source lead {0} is already merged into {1}").format(source, source_doc.merged_into))
	if target_doc.merged_into:
		frappe.throw(_("Target lead {0} is already merged into {1}").format(target, target_doc.merged_into))

	if target == source:
		frappe.throw(_("Cannot merge a lead into itself"))

	for doc in (source_doc, target_doc):
		if doc.converted:
			frappe.throw(_("Lead {0} is converted to a deal and cannot be merged").format(doc.name))

	field_snapshot = _snapshot_doc(target_doc)
	child_snapshot = _snapshot_child_tables(source_doc, target_doc)
	ref_snapshot = _snapshot_references(source_doc)

	_auto_merge_fields(target_doc, source_doc)

	_move_child_tables(source_doc, target_doc)

	_update_references(ref_snapshot, target_doc.name)

	target_doc.save(ignore_permissions=True)
	_sync_assignments(source, target)

	source_doc.db_set({"merged_into": target, "is_duplicate": 1})

	merge_log = frappe.get_doc(
		{
			"doctype": "CRM Merge Log",
			"reference_doctype": "CRM Lead",
			"target_document_name": target,
			"source_document_name": source,
			"field_snapshot": json.dumps(field_snapshot),
			"child_table_snapshot": json.dumps(child_snapshot.get("child_data")),
			"reference_snapshot": json.dumps(ref_snapshot),
		}
	)
	merge_log.insert(ignore_permissions=True)

	_update_timeline(source_doc.name, target, "merge", source_doc.lead_name, target_doc.lead_name)

	return {
		"target": target,
		"source": source,
		"merge_log": merge_log.name,
		"message": _("Lead {0} merged into {1}").format(source, target),
	}


@frappe.whitelist()
def split_lead(merge_log_name: str):
	merge_log = frappe.get_doc("CRM Merge Log", merge_log_name)

	if merge_log.split_at:
		frappe.throw(_("This merge has already been split"))

	target = merge_log.target_document_name
	source = merge_log.source_document_name

	if not frappe.has_permission("CRM Lead", "write", target):
		frappe.throw(_("Not allowed to modify target lead"), frappe.PermissionError)
	if not frappe.has_permission("CRM Lead", "write", source):
		frappe.throw(_("Not allowed to modify source lead"), frappe.PermissionError)

	field_snapshot = json.loads(merge_log.field_snapshot or "{}")
	child_data = json.loads(merge_log.child_table_snapshot or "{}")
	ref_data = json.loads(merge_log.reference_snapshot or "[]")

	target_doc = frappe.get_doc("CRM Lead", target)
	source_doc = frappe.get_doc("CRM Lead", source)

	if source_doc.merged_into != target:
		frappe.throw(_("Source lead {0} is not merged into {1}").format(source, target))
	if target_doc.merged_into:
		frappe.throw(_("Split the merge of {0} into {1} first").format(target, target_doc.merged_into))

	_restore_fields(target_doc, field_snapshot)

	target_doc.save(ignore_permissions=True)

	_move_child_tables_back(source_doc, target_doc, child_data)

	_restore_references(source, target, ref_data)
	_sync_assignments(source, target)

	source_doc.db_set({"merged_into": None, "is_duplicate": 0})
	merge_log.db_set({"split_at": frappe.utils.now(), "split_by": frappe.session.user})

	source_title = frappe.db.get_value("CRM Lead", source, "lead_name") or source
	target_title = frappe.db.get_value("CRM Lead", target, "lead_name") or target
	_update_timeline(source, target, "split", source_title, target_title)

	return {
		"target": target,
		"source": source,
		"message": _("Merge split: {0} and {1} restored").format(target, source),
	}


@frappe.whitelist()
def get_merge_history(lead_name: str):
	if not frappe.has_permission("CRM Lead", "read", lead_name):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	logs = frappe.get_all(
		"CRM Merge Log",
		filters={"reference_doctype": "CRM Lead"},
		or_filters={
			"target_document_name": lead_name,
			"source_document_name": lead_name,
		},
		fields=[
			"name",
			"target_document_name",
			"source_document_name",
			"merged_by",
			"merged_at",
			"split_at",
			"split_by",
		],
		order_by="creation desc",
	)
	if not logs:
		return []

	lead_names = {log.target_document_name for log in logs} | {log.source_document_name for log in logs}
	titles = dict(
		frappe.get_list(
			"CRM Lead", filters={"name": ("in", list(lead_names))}, fields=["name", "lead_name"], as_list=True
		)
	)
	return [
		{
			**log,
			"target_title": titles.get(log.target_document_name),
			"source_title": titles.get(log.source_document_name),
			"is_split": bool(log.split_at),
		}
		for log in logs
	]


_COMPARE_FIELDS = [
	"first_name",
	"last_name",
	"email",
	"mobile_no",
	"phone",
	"organization",
	"website",
	"territory",
	"industry",
	"job_title",
	"source",
	"lead_owner",
	"status",
	"no_of_employees",
	"annual_revenue",
	"salutation",
	"gender",
	"lost_reason",
	"lost_notes",
]


def _snapshot_doc(doc: frappe.model.document.Document) -> dict:
	return {f: _serializable(doc.get(f)) for f in _COMPARE_FIELDS}


def _serializable(obj):
	if isinstance(obj, datetime.date | datetime.datetime):
		return obj.isoformat()
	if isinstance(obj, datetime.time):
		return obj.isoformat()
	return obj


def _snapshot_child_tables(
	source_doc: frappe.model.document.Document,
	target_doc: frappe.model.document.Document,
) -> dict:
	child_tables = ["products", "status_change_log", "rolling_responses"]
	snapshots = {}

	for ct in child_tables:
		source_rows = source_doc.get(ct) or []
		target_rows = target_doc.get(ct) or []
		snapshots[ct] = {
			"source_table": source_doc.name,
			"target_table": target_doc.name,
			"source_rows": [
				{
					r.name: {
						f.fieldname: _serializable(r.get(f.fieldname))
						for f in r.meta.fields
						if f.fieldname != "name"
					}
				}
				for r in source_rows
			],
			"target_rows_count": len(target_rows),
			"source_rows_count": len(source_rows),
		}

	child_data = {}
	for ct in child_tables:
		source_rows = source_doc.get(ct) or []
		child_data[ct] = []
		for r in source_rows:
			row_data = {f.fieldname: _serializable(r.get(f.fieldname)) for f in r.meta.fields}
			row_data["name"] = r.name
			child_data[ct].append(row_data)

	return {"snapshots": snapshots, "child_data": child_data}


def _snapshot_references(source_doc: frappe.model.document.Document) -> list:
	source_name = source_doc.name
	refs = []

	refs.extend(_get_link_references("CRM Lead", source_name))
	refs.extend(_get_dynamic_link_references("CRM Lead", source_name))
	refs.extend(_get_file_references("CRM Lead", source_name))

	return refs


def _get_link_references(doctype: str, docname: str) -> list:
	references = []
	for field in get_link_fields(doctype):
		if field.issingle or (field.parent, field.fieldname) == ("CRM Lead", "merged_into"):
			continue
		for name in frappe.get_all(field.parent, filters={field.fieldname: docname}, pluck="name"):
			references.append(
				{"doctype": field.parent, "docname": name, "fieldname": field.fieldname, "old_value": docname}
			)
	return references


def _get_dynamic_link_references(doctype: str, docname: str) -> list:
	references = []
	for df in get_dynamic_link_map().get(doctype, []):
		meta = frappe.get_meta(df.parent)
		if meta.issingle or meta.is_virtual or df.parent == "CRM Merge Log":
			continue
		names = frappe.get_all(df.parent, filters={df.options: doctype, df.fieldname: docname}, pluck="name")
		for name in names:
			references.append(
				{"doctype": df.parent, "docname": name, "fieldname": df.fieldname, "old_value": docname}
			)
	return references


def _get_file_references(doctype: str, docname: str) -> list:
	names = frappe.get_all(
		"File", filters={"attached_to_doctype": doctype, "attached_to_name": docname}, pluck="name"
	)
	return [
		{"doctype": "File", "docname": name, "fieldname": "attached_to_name", "old_value": docname}
		for name in names
	]


def _update_references(refs: list, new_name: str):
	for ref in refs:
		frappe.db.set_value(ref["doctype"], ref["docname"], ref["fieldname"], new_name, update_modified=False)


def _restore_references(source_name: str, target_name: str, ref_data: list):
	for ref in ref_data:
		if ref.get("old_value") != source_name:
			continue
		if frappe.db.get_value(ref["doctype"], ref["docname"], ref["fieldname"]) != target_name:
			continue
		frappe.db.set_value(
			ref["doctype"], ref["docname"], ref["fieldname"], source_name, update_modified=False
		)


def _sync_assignments(*lead_names: str):
	for lead_name in lead_names:
		assignees = frappe.get_all(
			"ToDo",
			filters={
				"reference_type": "CRM Lead",
				"reference_name": lead_name,
				"status": ("not in", ("Cancelled", "Closed")),
				"allocated_to": ("is", "set"),
			},
			pluck="allocated_to",
			order_by="creation",
		)
		assignees = list(dict.fromkeys(assignees))
		frappe.db.set_value(
			"CRM Lead",
			lead_name,
			"_assign",
			json.dumps(assignees) if assignees else "",
			update_modified=False,
		)


def _move_child_tables(
	source_doc: frappe.model.document.Document,
	target_doc: frappe.model.document.Document,
):
	child_tables = ["products", "status_change_log", "rolling_responses"]

	for ct in child_tables:
		source_rows = source_doc.get(ct) or []
		for row in source_rows:
			row.parent = target_doc.name
			row.parenttype = target_doc.doctype

		target_rows = list(target_doc.get(ct) or [])
		target_rows.extend(source_rows)
		target_doc.set(ct, target_rows)


def _move_child_tables_back(
	source_doc: frappe.model.document.Document,
	target_doc: frappe.model.document.Document,
	child_data: dict,
):
	child_tables = ["products", "status_change_log", "rolling_responses"]

	for ct in child_tables:
		child_doctype = target_doc.meta.get_field(ct).options
		source_rows = child_data.get(ct) or []
		for row_data in source_rows:
			row_name = row_data.get("name")
			if not row_name:
				continue
			parent = frappe.db.get_value(child_doctype, row_name, ["parent", "parenttype"])
			if parent != (target_doc.name, target_doc.doctype):
				continue
			frappe.db.set_value(
				child_doctype,
				row_name,
				{"parent": source_doc.name, "parenttype": source_doc.doctype},
			)


def _auto_merge_fields(
	target_doc: frappe.model.document.Document,
	source_doc: frappe.model.document.Document,
):
	for field in _COMPARE_FIELDS:
		source_val = source_doc.get(field)
		if source_val:
			target_doc.set(field, source_val)


def _restore_fields(
	target_doc: frappe.model.document.Document,
	snapshot: dict,
):
	for fieldname in _COMPARE_FIELDS:
		if fieldname in snapshot:
			target_doc.set(fieldname, snapshot[fieldname])


def _update_timeline(
	source: str, target: str, action: str, source_title: str | None = None, target_title: str | None = None
):
	src = source_title or source
	tgt = target_title or target

	if action == "merge":
		comment_text = _("{0} merged into {1}").format(src, tgt)
		frappe.get_doc(
			{
				"doctype": "Comment",
				"comment_type": "Info",
				"reference_doctype": "CRM Lead",
				"reference_name": target,
				"content": comment_text,
			}
		).insert(ignore_permissions=True)
		frappe.get_doc(
			{
				"doctype": "Comment",
				"comment_type": "Info",
				"reference_doctype": "CRM Lead",
				"reference_name": source,
				"content": _("{0} merged into {1}").format(src, tgt),
			}
		).insert(ignore_permissions=True)
	elif action == "split":
		frappe.get_doc(
			{
				"doctype": "Comment",
				"comment_type": "Info",
				"reference_doctype": "CRM Lead",
				"reference_name": target,
				"content": _("{0} split from {1}").format(src, tgt),
			}
		).insert(ignore_permissions=True)
		frappe.get_doc(
			{
				"doctype": "Comment",
				"comment_type": "Info",
				"reference_doctype": "CRM Lead",
				"reference_name": source,
				"content": _("{0} split from {1}").format(src, tgt),
			}
		).insert(ignore_permissions=True)
