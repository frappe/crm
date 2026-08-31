import frappe
from frappe import _

DISPOSITIONS = ["Interested", "Not Interested", "No Answer", "Callback", "Voicemail", "Wrong Number"]


def _get_session(name: str):
	doc = frappe.get_doc("CRM Dial Session", name)
	if doc.agent != frappe.session.user and "Sales Manager" not in frappe.get_roles():
		frappe.throw(_("This dial session belongs to another agent"), frappe.PermissionError)
	return doc


def _session_payload(doc) -> dict:
	entries = [
		{
			"idx": e.idx,
			"reference_doctype": e.reference_doctype,
			"reference_name": e.reference_name,
			"display_name": e.display_name,
			"number": e.number,
			"status": e.status,
			"disposition": e.disposition,
			"note": e.note,
		}
		for e in doc.entries
	]
	done = len([e for e in entries if e["status"] != "Pending"])
	current = next((e for e in entries if e["status"] == "Pending"), None)
	return {
		"name": doc.name,
		"title": doc.title,
		"status": doc.status,
		"source_doctype": doc.source_doctype,
		"total": len(entries),
		"done": done,
		"current": current,
		"entries": entries,
		"dispositions": DISPOSITIONS,
	}


@frappe.whitelist()
def get_active_session() -> dict | None:
	name = frappe.db.get_value("CRM Dial Session", {"agent": frappe.session.user, "status": "In Progress"})
	return _session_payload(frappe.get_doc("CRM Dial Session", name)) if name else None


@frappe.whitelist(methods=["POST"])
def create_session(
	doctype: str = "CRM Lead", status: str | None = None, limit: int = 20, title: str | None = None
) -> dict:
	"""Build a call queue from the newest records (with a phone number) of a status."""
	if doctype not in ("CRM Lead", "CRM Deal"):
		frappe.throw(_("Invalid doctype"))
	if frappe.db.exists("CRM Dial Session", {"agent": frappe.session.user, "status": "In Progress"}):
		frappe.throw(_("You already have a dial session in progress. Finish or cancel it first."))

	filters = {"mobile_no": ["is", "set"]}
	if doctype == "CRM Lead":
		filters["converted"] = 0
	if status:
		filters["status"] = status
	name_field = "lead_name" if doctype == "CRM Lead" else "organization"
	rows = frappe.get_list(
		doctype,
		filters=filters,
		fields=["name", "mobile_no", name_field],
		order_by="modified desc",
		page_length=min(int(limit), 100),
	)
	if not rows:
		frappe.throw(_("No records with a phone number match the selection"))

	doc = frappe.get_doc(
		{
			"doctype": "CRM Dial Session",
			"agent": frappe.session.user,
			"status": "In Progress",
			"source_doctype": doctype,
			"title": title or _("{0} · {1} records").format(status or _("All"), len(rows)),
			"entries": [
				{
					"reference_doctype": doctype,
					"reference_name": row.name,
					"display_name": row.get(name_field) or row.name,
					"number": row.mobile_no,
					"status": "Pending",
				}
				for row in rows
			],
		}
	)
	doc.insert()
	return _session_payload(doc)


@frappe.whitelist(methods=["POST"])
def complete_entry(
	session: str, idx: int, disposition: str | None = None, note: str | None = None, skipped: bool = False
) -> dict:
	"""Record the outcome of the current call and move on."""
	if disposition and disposition not in DISPOSITIONS:
		frappe.throw(_("Invalid disposition"))
	doc = _get_session(session)
	entry = next((e for e in doc.entries if e.idx == int(idx)), None)
	if not entry:
		frappe.throw(_("Entry not found"))
	entry.status = "Skipped" if frappe.utils.sbool(skipped) else "Done"
	entry.disposition = disposition or ""
	entry.note = (note or "").strip()

	if entry.status == "Done" and (entry.disposition or entry.note):
		_log_outcome_on_record(entry)

	if all(e.status != "Pending" for e in doc.entries):
		doc.status = "Completed"
	doc.save(ignore_permissions=True)
	return _session_payload(doc)


def _log_outcome_on_record(entry) -> None:
	try:
		ref = frappe.get_doc(entry.reference_doctype, entry.reference_name)
		parts = [_("Call outcome: {0}").format(_(entry.disposition or "-"))]
		if entry.note:
			parts.append(frappe.utils.escape_html(entry.note))
		ref.add_comment("Comment", "<br>".join(parts))
	except Exception:
		frappe.log_error(frappe.get_traceback(), "CRM Dialer: failed to log outcome")


@frappe.whitelist(methods=["POST"])
def end_session(session: str, cancel: bool = False) -> dict:
	doc = _get_session(session)
	doc.status = "Cancelled" if frappe.utils.sbool(cancel) else "Completed"
	doc.save(ignore_permissions=True)
	return _session_payload(doc)
