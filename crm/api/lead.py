import datetime
import json

import frappe
from frappe import _
from frappe.model.dynamic_links import get_dynamic_link_map


@frappe.whitelist()
def create_lead(doc: str | dict):
	if isinstance(doc, str):
		doc = json.loads(doc)

	lead = frappe.get_doc({"doctype": "CRM Lead", **doc})
	lead.insert(ignore_permissions=True)

	duplicates = find_duplicate_leads(lead.name)

	return {
		"name": lead.name,
		"duplicate_warning": len(duplicates) > 0,
		"possible_duplicates": duplicates,
	}


@frappe.whitelist()
def find_duplicate_leads(lead_name: str):
	lead = frappe.get_cached_doc("CRM Lead", lead_name)
	matches = []

	filters = [
		["name", "!=", lead_name],
		["merged_into", "is", "not set"],
		["is_duplicate", "=", 0],
	]

	match_fields = []
	if lead.email:
		match_fields.append("email")
	if lead.mobile_no:
		match_fields.append("mobile_no")
	if lead.phone:
		match_fields.append("phone")

	if not match_fields:
		return []

	or_filters = []
	for field in match_fields:
		or_filters.append([field, "=", lead.get(field)])

	possible = frappe.get_all(
		"CRM Lead",
		filters=filters,
		or_filters=or_filters,
		fields=["name", "lead_name", "email", "mobile_no", "phone", "organization"],
		limit=20,
	)

	for p in possible:
		matched = []
		for field in match_fields:
			if p.get(field) and p[field] == lead.get(field):
				matched.append(field)
		matches.append({**p, "matched_fields": matched})

	return matches


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

	if target == source:
		frappe.throw(_("Cannot merge a lead into itself"))

	field_snapshot = _snapshot_doc(target_doc)
	child_snapshot = _snapshot_child_tables(source_doc, target_doc)
	ref_snapshot = _snapshot_references(source_doc)

	_auto_merge_fields(target_doc, source_doc)

	_move_child_tables(source_doc, target_doc)

	_update_references(source_doc.name, target_doc.name)

	target_doc.save(ignore_permissions=True)

	source_doc.db_set("merged_into", target)
	source_doc.db_set("is_duplicate", 1)

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

	_restore_fields(target_doc, field_snapshot)

	target_doc.save(ignore_permissions=True)

	_move_child_tables_back(source_doc, target_doc, child_data)

	_restore_references(source, target, ref_data)

	source_doc.db_set("merged_into", None)
	source_doc.db_set("is_duplicate", 0)

	merge_log.db_set("split_at", frappe.utils.now())
	merge_log.db_set("split_by", frappe.session.user)

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

	target_title_map = {}
	for log in logs:
		for l, key in [(log, "target_document_name"), (log, "source_document_name")]:
			if l[key] not in target_title_map:
				doc = frappe.db.get_value("CRM Lead", l[key], "lead_name")
				target_title_map[l[key]] = doc

	result = []
	for log in logs:
		result.append(
			{
				**log,
				"target_title": target_title_map.get(log.target_document_name),
				"source_title": target_title_map.get(log.source_document_name),
				"is_split": bool(log.split_at),
			}
		)

	return result


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

	return refs


def _get_link_references(doctype: str, docname: str) -> list:
	references = []
	fields = frappe.db.get_all(
		"DocField",
		filters={"fieldtype": "Link", "options": doctype},
		fields=["parent", "fieldname"],
	)

	seen = set()
	for f in fields:
		parent = f.get("parent")
		if not parent:
			continue
		key = (parent, f["fieldname"])
		if key in seen:
			continue
		seen.add(key)
		try:
			names = frappe.get_all(
				parent,
				filters={f["fieldname"]: docname},
				pluck="name",
				limit=50,
			)
			for name in names:
				references.append(
					{
						"doctype": parent,
						"docname": name,
						"fieldname": f["fieldname"],
						"old_value": docname,
					}
				)
		except Exception:
			continue

	return references


def _get_dynamic_link_references(doctype: str, docname: str) -> list:
	references = []
	dynamic_link_map = get_dynamic_link_map()

	for df in dynamic_link_map.get(doctype, []):
		df_doctype = df.get("parent")
		df_fieldname = df.get("fieldname")
		if not df_doctype or not df_fieldname:
			continue
		try:
			names = frappe.get_all(
				df_doctype,
				filters={df_fieldname: docname},
				pluck="name",
				limit=50,
			)
			for name in names:
				ref = None
				if df.get("parentfield"):
					parent_doc = frappe.db.get_value(df_doctype, name, "parent")
					parent_doctype = frappe.db.get_value(df_doctype, name, "parenttype")
					if parent_doc and parent_doctype:
						ref = {
							"child_doctype": df_doctype,
							"parent_doctype": parent_doctype,
							"parent_docname": parent_doc,
							"child_name": name,
							"fieldname": df_fieldname,
							"old_value": docname,
						}
				if not ref:
					ref = {
						"doctype": df_doctype,
						"docname": name,
						"fieldname": df_fieldname,
						"old_value": docname,
					}
				references.append(ref)
		except Exception:
			continue

	return references


def _update_references(old_name: str, new_name: str):
	for ref in _get_link_references("CRM Lead", old_name):
		try:
			frappe.db.set_value(ref["doctype"], ref["docname"], ref["fieldname"], new_name)
		except Exception:
			continue

	for ref in _get_dynamic_link_references("CRM Lead", old_name):
		try:
			if "child_doctype" in ref:
				frappe.db.set_value(
					ref["child_doctype"],
					ref["child_name"],
					ref["fieldname"],
					new_name,
				)
			else:
				frappe.db.set_value(ref["doctype"], ref["docname"], ref["fieldname"], new_name)
		except Exception:
			continue


def _restore_references(target_name: str, source_name: str, ref_data: list):
	for ref in ref_data:
		if ref.get("old_value") != target_name:
			continue
		try:
			if "child_doctype" in ref:
				frappe.db.set_value(
					ref["child_doctype"],
					ref["child_name"],
					ref["fieldname"],
					source_name,
				)
			else:
				frappe.db.set_value(ref["doctype"], ref["docname"], ref["fieldname"], source_name)
		except Exception:
			continue


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
			row.db_update()

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
		source_rows = child_data.get(ct) or []
		for row_data in source_rows:
			row_name = row_data.get("name")
			if not row_name:
				continue
			if not frappe.db.exists(ct, row_name):
				continue
			frappe.db.set_value(
				ct,
				row_name,
				{"parent": source_doc.name, "parenttype": source_doc.doctype},
			)

		target_child_rows = target_doc.get(ct) or []
		source_names = {r["name"] for r in source_rows if r.get("name")}
		target_doc.set(
			ct,
			[r for r in target_child_rows if r.name not in source_names],
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
	for fieldname, value in snapshot.items():
		target_doc.set(fieldname, value)


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
