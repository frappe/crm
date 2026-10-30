import json
from collections import defaultdict

import frappe
from frappe.model import default_fields, no_value_fields, table_fields
from frappe.model.document import Document
from frappe.model.dynamic_links import get_dynamic_links
from frappe.model.rename_doc import get_link_fields
from frappe.utils import cstr, flt, strip_html
from frappe.utils.formatters import format_value

MERGE_CONFIG = {
	"CRM Lead": {
		# status_change_log and rolling_responses stay with their lead: the status log and the SLA
		# both extend the lead's own last row, so moved rows would be closed in the target's place.
		"child_tables": ["products"],
		# Never merged or restored on top of the defaults: their values drive hooks (sharing,
		# assignment, SLA, status logs) or describe the lead itself rather than its contact data.
		"denylist": {
			"lead_owner",
			"status",
			"lost_reason",
			"sla",
			"sla_creation",
			"sla_status",
			"response_by",
			"first_responded_on",
			"first_response_time",
			"communication_status",
			"lead_name",
			"title",
			"converted",
			"merged_into",
			"is_duplicate",
			"naming_series",
			# automation scoring state, not contact data
			"lead_score",
			"lead_temperature",
			# Facebook sync dedupes a campaign on it
			"facebook_form_id",
			# belongs with lost_reason
			"lost_notes",
		},
		# Points a merged document at its target; never re-pointed by a later merge
		"merged_into_field": "merged_into",
		"match_keys": {"email": ["email"], "phone": ["mobile_no", "phone"]},
	},
}


def merge_documents(
	target_doc: Document, source_doc: Document, take_from_source: list[str] | None = None
) -> Document:
	"""Fill the target's empty fields from the source and move the source's child rows and every
	reference to it onto the target. Fields in take_from_source get the source's value even when
	the target has one. Returns the CRM Merge Log that split_documents undoes.
	Callers check permissions and lock both documents first."""
	writable = _writable_fields(target_doc)
	if invalid := set(take_from_source or []) - set(writable):
		frappe.throw(
			frappe._("Cannot take these fields from the merged lead: {0}").format(", ".join(sorted(invalid)))
		)

	merge_log = frappe.get_doc(
		{
			"doctype": "CRM Merge Log",
			"reference_doctype": target_doc.doctype,
			"target_document_name": target_doc.name,
			"source_document_name": source_doc.name,
			"field_snapshot": frappe.as_json(_snapshot_doc(target_doc), indent=None),
			"child_table_snapshot": json.dumps(_snapshot_child_tables(source_doc)),
		}
	)
	refs = _snapshot_references(source_doc)
	merge_log.reference_snapshot = json.dumps(refs)

	# After the snapshot, so a split restores the target's own value for these too
	for field in take_from_source or []:
		target_doc.set(field, source_doc.get(field))
	_auto_merge_fields(target_doc, source_doc)
	_move_child_tables(source_doc, target_doc)
	_repoint(refs, target_doc.doctype, source_doc.name, target_doc.name)
	merge_log.merge_version = _save_with_version(target_doc)
	_sync_assignments(target_doc.doctype, source_doc.name, target_doc.name)
	_sync_product_totals(target_doc.doctype, source_doc.name, target_doc.name)

	merge_log.insert(ignore_permissions=True)
	return merge_log


def split_documents(merge_log: Document, target_doc: Document, source_doc: Document):
	"""Undo merge_documents: restore the target's fields that still hold the merged-in value and
	move the source's child rows and references back. Callers check permissions and lock first."""
	_restore_fields(target_doc, source_doc, json.loads(merge_log.field_snapshot or "{}"))

	# Before the save, so validations that look at linked records (e.g. the WhatsApp
	# recipient guard) no longer see the source's records on the target.
	allowed = _reference_fields(target_doc.doctype)
	refs = [
		ref
		for ref in json.loads(merge_log.reference_snapshot or "[]")
		if ref.get("old_value") == source_doc.name and (ref.get("doctype"), ref.get("fieldname")) in allowed
	]
	_repoint(refs, target_doc.doctype, target_doc.name, source_doc.name)

	split_version = _save_with_version(target_doc)
	_move_child_tables_back(source_doc, target_doc, json.loads(merge_log.child_table_snapshot or "{}"))
	_sync_assignments(target_doc.doctype, source_doc.name, target_doc.name)
	_sync_product_totals(target_doc.doctype, source_doc.name, target_doc.name)

	merge_log.db_set(
		{"split_at": frappe.utils.now(), "split_by": frappe.session.user, "split_version": split_version}
	)


def _save_with_version(doc: Document) -> str | None:
	"""Save, writing a Version even in tests, and return that Version's name, or None when the
	save changed nothing. The activity feed shows it inside the merge or split entry instead of
	as a field change of its own."""
	before = _latest_version(doc)
	doc.save(ignore_permissions=True, ignore_version=False)
	after = _latest_version(doc)
	return after if after != before else None


def _latest_version(doc: Document) -> str | None:
	return frappe.db.get_value(
		"Version", {"ref_doctype": doc.doctype, "docname": doc.name}, "name", order_by="creation desc"
	)


def _mergeable_fields(doctype: str) -> list[str]:
	"""Value fields a merge fills on the target and a split restores, custom fields included.
	Unique fields are left out: the source keeps its value, so a copy could never be saved."""
	denylist = MERGE_CONFIG[doctype]["denylist"] | set(default_fields)
	return [
		df.fieldname
		for df in frappe.get_meta(doctype).fields
		if df.fieldtype not in no_value_fields
		and df.fieldtype not in table_fields
		and not df.no_copy
		and not df.read_only
		and not df.unique
		and df.fieldname not in denylist
	]


def _snapshot_doc(doc: Document) -> dict:
	return {f: doc.get(f) for f in _mergeable_fields(doc.doctype)}


def _snapshot_child_tables(source_doc: Document) -> dict:
	return {
		ct: [row.name for row in source_doc.get(ct) or []]
		for ct in MERGE_CONFIG[source_doc.doctype]["child_tables"]
	}


def _snapshot_references(source_doc: Document) -> list:
	source_name = source_doc.name
	refs = []

	refs.extend(_get_link_references(source_doc.doctype, source_name))
	refs.extend(_get_dynamic_link_references(source_doc.doctype, source_name))
	refs.extend(_get_file_references(source_doc.doctype, source_name))

	return refs


def _link_fields(doctype: str) -> list:
	merged_into = (doctype, MERGE_CONFIG[doctype]["merged_into_field"])
	return [
		field
		for field in get_link_fields(doctype)
		if not field.issingle and (field.parent, field.fieldname) != merged_into
	]


def _reference_fields(doctype: str) -> dict[tuple[str, str], str | None]:
	"""(doctype, fieldname) pairs a merge can re-point, so a split never writes any other field,
	each mapped to the field naming its doctype for a dynamic link (None for a plain Link)."""
	fields = {(field.parent, field.fieldname): None for field in _link_fields(doctype)}
	fields |= {
		(df.parent, df.fieldname): df.options for df in get_dynamic_links() if df.parent != "CRM Merge Log"
	}
	fields[("File", "attached_to_name")] = "attached_to_doctype"
	return fields


def _get_link_references(doctype: str, docname: str) -> list:
	references = []
	for field in _link_fields(doctype):
		for name in frappe.get_all(field.parent, filters={field.fieldname: docname}, pluck="name"):
			references.append(
				{"doctype": field.parent, "docname": name, "fieldname": field.fieldname, "old_value": docname}
			)
	return references


def _get_dynamic_link_references(doctype: str, docname: str) -> list:
	"""Rows whose Dynamic Link points at the document. Read from the field metadata, not
	frappe's dynamic link map: that map is filtered by a cached list of the doctypes each
	field already links to, which rows written without a normal insert never update."""
	references = []
	for df in get_dynamic_links():
		meta = frappe.get_meta(df.parent)
		if meta.issingle or meta.is_virtual or df.parent == "CRM Merge Log":
			continue
		if not _can_link_to(meta.get_field(df.options), doctype) or not frappe.db.table_exists(df.parent):
			continue
		names = frappe.get_all(df.parent, filters={df.options: doctype, df.fieldname: docname}, pluck="name")
		for name in names:
			references.append(
				{"doctype": df.parent, "docname": name, "fieldname": df.fieldname, "old_value": docname}
			)
	return references


def _can_link_to(options_field, doctype: str) -> bool:
	"""Whether the field naming a Dynamic Link's doctype can hold this doctype."""
	if not options_field:
		return False
	if options_field.fieldtype == "Link":
		return options_field.options == "DocType"
	if options_field.fieldtype == "Select":
		return doctype in (options_field.options or "").split("\n")
	return options_field.fieldtype == "Data"


def _get_file_references(doctype: str, docname: str) -> list:
	names = frappe.get_all(
		"File", filters={"attached_to_doctype": doctype, "attached_to_name": docname}, pluck="name"
	)
	return [
		{"doctype": "File", "docname": name, "fieldname": "attached_to_name", "old_value": docname}
		for name in names
	]


def _repoint(refs: list, doctype: str, from_name: str, to_name: str):
	"""One UPDATE per (doctype, fieldname). Only rows that still point at doctype's from_name
	change, so a split leaves alone a row that was pointed elsewhere after the merge, including
	a dynamic link moved to another doctype's record that happens to share the name."""
	type_fields = _reference_fields(doctype)
	groups = defaultdict(list)
	for ref in refs:
		if ref.get("docname"):
			groups[(ref["doctype"], ref["fieldname"])].append(ref["docname"])
	for (ref_doctype, fieldname), names in groups.items():
		filters = {"name": ("in", names), fieldname: from_name}
		if type_field := type_fields.get((ref_doctype, fieldname)):
			filters[type_field] = doctype
		frappe.db.set_value(ref_doctype, filters, fieldname, to_name, update_modified=False)


def _sync_assignments(doctype: str, *names: str):
	for name in names:
		assignees = frappe.get_all(
			"ToDo",
			filters={
				"reference_type": doctype,
				"reference_name": name,
				"status": ("not in", ("Cancelled", "Closed")),
				"allocated_to": ("is", "set"),
			},
			pluck="allocated_to",
			order_by="creation",
		)
		assignees = list(dict.fromkeys(assignees))
		frappe.db.set_value(
			doctype,
			name,
			"_assign",
			json.dumps(assignees) if assignees else "",
			update_modified=False,
		)


def _sync_product_totals(doctype: str, *names: str):
	"""total and net_total are read-only and summed only by the form script, so recompute them
	the same way once a merge or split has moved product rows."""
	if "products" not in MERGE_CONFIG[doctype]["child_tables"]:
		return
	child_doctype = frappe.get_meta(doctype).get_field("products").options
	for name in names:
		rows = frappe.get_all(
			child_doctype,
			filters={"parent": name, "parenttype": doctype, "parentfield": "products"},
			fields=["amount", "net_amount", "discount_percentage"],
		)
		total = sum(flt(row.amount) for row in rows)
		net_total = sum(flt(row.net_amount) for row in rows)
		discount_applied = any(flt(row.discount_percentage) > 0 for row in rows)
		frappe.db.set_value(
			doctype,
			name,
			{"total": total, "net_total": net_total if net_total or discount_applied else total},
			update_modified=False,
		)


def _move_child_tables(source_doc: Document, target_doc: Document):
	child_tables = MERGE_CONFIG[target_doc.doctype]["child_tables"]

	for ct in child_tables:
		source_rows = source_doc.get(ct) or []
		for row in source_rows:
			row.parent = target_doc.name
			row.parenttype = target_doc.doctype

		target_rows = list(target_doc.get(ct) or [])
		target_rows.extend(source_rows)
		target_doc.set(ct, target_rows)


def _move_child_tables_back(source_doc: Document, target_doc: Document, child_data: dict):
	child_tables = MERGE_CONFIG[target_doc.doctype]["child_tables"]

	for ct in child_tables:
		child_doctype = target_doc.meta.get_field(ct).options
		for row in child_data.get(ct) or []:
			# Logs written before names-only snapshots hold whole rows
			row_name = row.get("name") if isinstance(row, dict) else row
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


def _writable_fields(target_doc: Document) -> list[str]:
	"""Mergeable fields the session user may write on the target."""
	fields = []
	for field in _mergeable_fields(target_doc.doctype):
		df = target_doc.meta.get_field(field)
		if df.permlevel and not target_doc.has_permlevel_access_to(field, df, "write"):
			continue
		fields.append(field)
	return fields


def get_field_differences(target_doc: Document, source_doc: Document) -> list[dict]:
	"""Fields a merge would decide between, with values formatted as plain text for display.
	A field set on only one side is filled automatically; one set on both is the user's pick."""
	differences = []
	for field in _writable_fields(target_doc):
		target_val, source_val = target_doc.get(field), source_doc.get(field)
		if (not target_val and not source_val) or target_val == source_val:
			continue
		df = target_doc.meta.get_field(field)
		differences.append(
			{
				"fieldname": field,
				"label": frappe._(df.label) if df.label else field,
				"fieldtype": df.fieldtype,
				"options": df.options,
				"source_value": source_val,
				"target_value": target_val,
				"source_display": _display_value(source_val, df, source_doc),
				"target_display": _display_value(target_val, df, target_doc),
			}
		)
	return differences


def _display_value(value, df, doc) -> str:
	if not value:
		return ""
	if df.fieldtype == "Check":
		return frappe._("Yes")
	# format_value returns markup for text editor / long text fields
	return strip_html(cstr(format_value(value, df, doc))).strip()


def _auto_merge_fields(target_doc: Document, source_doc: Document):
	for field in _writable_fields(target_doc):
		source_val = source_doc.get(field)
		if source_val and not target_doc.get(field):
			target_doc.set(field, source_val)


def _restore_fields(target_doc: Document, source_doc: Document, snapshot: dict):
	for fieldname in _mergeable_fields(target_doc.doctype):
		df = target_doc.meta.get_field(fieldname)
		if df.permlevel and not target_doc.has_permlevel_access_to(fieldname, df, "write"):
			continue
		if fieldname in snapshot and target_doc.get(fieldname) == source_doc.get(fieldname):
			target_doc.set(fieldname, snapshot[fieldname])
