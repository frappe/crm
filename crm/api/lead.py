import frappe
from frappe import _

from crm.api.merge import MERGE_CONFIG, merge_documents, split_documents
from crm.fcrm.doctype.crm_lead.crm_lead import lock_lead
from crm.integrations.api import find_by_phone
from crm.utils import normalize_phone

MAX_SEARCH_LIMIT = 50


@frappe.whitelist()
def find_duplicate_leads(lead_name: str):
	if not frappe.has_permission("CRM Lead", "read", lead_name):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	lead = frappe.get_cached_doc("CRM Lead", lead_name)
	match_keys = MERGE_CONFIG["CRM Lead"]["match_keys"]

	candidates = set()
	for field in match_keys["email"]:
		if lead.get(field):
			# LIKE, not =, so the match ignores case on Postgres as well
			match = [[field, "like", _escape_like(lead.get(field))]]
			candidates.update(frappe.get_all("CRM Lead", filters=match, pluck="name"))
	for field in match_keys["phone"]:
		if lead.get(field):
			candidates.update(
				m["docname"] for m in find_by_phone(lead.get(field)) if m["doctype"] == "CRM Lead"
			)
	candidates.discard(lead_name)
	if not candidates:
		return []

	possible = frappe.get_list(
		"CRM Lead",
		filters={"name": ("in", list(candidates)), "converted": 0, "is_duplicate": 0},
		fields=["name", "lead_name", *match_keys["email"], *match_keys["phone"], "organization"],
		limit=20,
	)

	numbers = {normalize_phone(lead.get(f)) for f in match_keys["phone"]} - {""}
	return [{**p, "matched_fields": _matched_fields(lead, p, numbers, match_keys)} for p in possible]


def _matched_fields(lead, candidate, numbers: set, match_keys: dict) -> list:
	matched = []
	for field in match_keys["email"]:
		if lead.get(field) and (candidate.get(field) or "").lower() == lead.get(field).lower():
			matched.append(field)
	for field in match_keys["phone"]:
		if normalize_phone(candidate.get(field)) in numbers:
			matched.append(field)
	return matched


@frappe.whitelist()
def search_mergeable_leads(txt: str = "", current_lead: str = "", limit: int = 20):
	user = frappe.session.user
	limit = min(max(limit, 1), MAX_SEARCH_LIMIT)

	filters = [["is_duplicate", "=", 0], ["converted", "=", 0]]
	if current_lead:
		filters.append(["name", "!=", current_lead])

	or_filters = None
	if txt:
		pattern = f"%{_escape_like(txt)}%"
		or_filters = [[field, "like", pattern] for field in ("name", "lead_name", "email", "organization")]

	candidates = []
	for assignment in (["_assign", "like", f'%"{user}"%'], ["_assign", "is", "not set"]):
		candidates += frappe.get_list(
			"CRM Lead",
			filters=[*filters, assignment],
			or_filters=or_filters,
			fields=["name", "lead_name", "email", "organization", "modified"],
			order_by="modified desc",
			limit=limit,
		)
	candidates.sort(key=lambda r: r.modified, reverse=True)

	return [
		{
			"value": r["name"],
			"label": r.get("lead_name") or r["name"],
			"description": r.get("email") or r.get("organization") or "",
		}
		for r in candidates[:limit]
	]


def _escape_like(txt: str) -> str:
	return txt.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


@frappe.whitelist(methods=["POST"])
def merge_leads(target: str, source: str):
	if target == source:
		frappe.throw(_("Cannot merge a lead into itself"))
	if not frappe.has_permission("CRM Lead", "write", target):
		frappe.throw(_("Not allowed to modify target lead"), frappe.PermissionError)
	if not frappe.has_permission("CRM Lead", "write", source):
		frappe.throw(_("Not allowed to modify source lead"), frappe.PermissionError)

	target_doc, source_doc = lock_lead(target, source)

	if source_doc.merged_into:
		frappe.throw(_("Source lead {0} is already merged into {1}").format(source, source_doc.merged_into))
	if target_doc.merged_into:
		frappe.throw(_("Target lead {0} is already merged into {1}").format(target, target_doc.merged_into))

	for doc in (source_doc, target_doc):
		if doc.converted:
			frappe.throw(_("Lead {0} is converted to a deal and cannot be merged").format(doc.name))

	merge_log = merge_documents(target_doc, source_doc)
	source_doc.db_set({"merged_into": target, "is_duplicate": 1})

	message = _("{0} merged into {1}").format(source_doc.lead_name or source, target_doc.lead_name or target)
	for doc in (target_doc, source_doc):
		doc.add_comment("Info", message)

	return {
		"target": target,
		"source": source,
		"merge_log": merge_log.name,
		"message": _("Lead {0} merged into {1}").format(source, target),
	}


@frappe.whitelist(methods=["POST"])
def split_lead(merge_log_name: str):
	merge_log = frappe.get_doc("CRM Merge Log", merge_log_name)
	target = merge_log.target_document_name
	source = merge_log.source_document_name

	if not frappe.has_permission("CRM Lead", "write", target):
		frappe.throw(_("Not allowed to modify target lead"), frappe.PermissionError)
	if not frappe.has_permission("CRM Lead", "write", source):
		frappe.throw(_("Not allowed to modify source lead"), frappe.PermissionError)

	target_doc, source_doc = lock_lead(target, source)

	# Read under the leads' lock: a split and re-merge of the same pair that ran while this
	# request waited would otherwise pass the checks below and get this log's old snapshots.
	merge_log = frappe.get_doc("CRM Merge Log", merge_log_name, for_update=True)
	if merge_log.split_at:
		frappe.throw(_("This merge has already been split"))
	if source_doc.merged_into != target:
		frappe.throw(_("Source lead {0} is not merged into {1}").format(source, target))
	if target_doc.merged_into:
		frappe.throw(_("Split the merge of {0} into {1} first").format(target, target_doc.merged_into))
	if target_doc.converted:
		frappe.throw(_("Lead {0} is converted to a deal, so this merge cannot be split").format(target))

	split_documents(merge_log, target_doc, source_doc)
	source_doc.db_set({"merged_into": None, "is_duplicate": 0})

	message = _("{0} split from {1}").format(source_doc.lead_name or source, target_doc.lead_name or target)
	for doc in (target_doc, source_doc):
		doc.add_comment("Info", message)

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
