import frappe
from frappe.utils import get_datetime, now_datetime

from crm.api.reply_alerts import Reply, alert_assignees

DIRECTION_FIELDS = {"Inbound": "last_inbound_at", "Outbound": "last_outbound_at"}


def record(doctype: str, docname: str, direction: str, at=None, reply: Reply | None = None):
	"""Record an inbound or outbound message on a lead or deal, forwarding converted leads to their deal.

	A `reply` alerts the assignees, once, on the deal for a converted lead. Messages older than
	the last one recorded raise no alert: they arrive late, out of order or from a resync.
	"""
	if doctype not in ("CRM Lead", "CRM Deal") or direction not in DIRECTION_FIELDS:
		return

	field = DIRECTION_FIELDS[direction]
	at = get_datetime(at or now_datetime())
	newer = _set_if_newer(doctype, docname, field, at)

	if doctype == "CRM Lead" and frappe.db.get_value("CRM Lead", docname, "converted"):
		deal = get_latest_deal(docname)
		if deal:
			doctype, docname = "CRM Deal", deal
			newer = _set_if_newer(doctype, docname, field, at)

	if reply and newer and direction == "Inbound":
		alert_assignees(doctype, docname, reply)


def get_latest_deal(lead: str) -> str | None:
	deals = frappe.get_all(
		"CRM Deal", filters={"lead": lead}, order_by="creation desc", limit=1, pluck="name"
	)
	return deals[0] if deals else None


def get_awaiting_reply_since(last_inbound_at, last_outbound_at):
	if last_inbound_at and (not last_outbound_at or last_inbound_at > last_outbound_at):
		return last_inbound_at
	return None


def _set_if_newer(doctype: str, docname: str, field: str, at) -> bool:
	row = frappe.db.get_value(doctype, docname, list(DIRECTION_FIELDS.values()), as_dict=True)
	if not row or (row[field] and row[field] >= at):
		return False

	row[field] = at
	frappe.db.set_value(
		doctype,
		docname,
		{
			field: at,
			"awaiting_reply_since": get_awaiting_reply_since(row.last_inbound_at, row.last_outbound_at),
		},
		update_modified=False,
	)
	return True
