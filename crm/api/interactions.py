import frappe
from frappe.utils import get_datetime, now_datetime

DIRECTION_FIELDS = {"Inbound": "last_inbound_at", "Outbound": "last_outbound_at"}


def record(doctype: str, docname: str, direction: str, at=None):
	"""Record an inbound or outbound message on a lead or deal, forwarding converted leads to their deal."""
	if doctype not in ("CRM Lead", "CRM Deal") or direction not in DIRECTION_FIELDS:
		return

	field = DIRECTION_FIELDS[direction]
	at = get_datetime(at or now_datetime())
	_move_forward(doctype, docname, field, at)

	if doctype == "CRM Lead" and frappe.db.get_value("CRM Lead", docname, "converted"):
		deal = get_latest_deal(docname)
		if deal:
			_move_forward("CRM Deal", deal, field, at)


def get_latest_deal(lead: str) -> str | None:
	deals = frappe.get_all(
		"CRM Deal", filters={"lead": lead}, order_by="creation desc", limit=1, pluck="name"
	)
	return deals[0] if deals else None


def get_awaiting_reply_since(last_inbound_at, last_outbound_at):
	if last_inbound_at and (not last_outbound_at or last_inbound_at > last_outbound_at):
		return last_inbound_at
	return None


def _move_forward(doctype: str, docname: str, field: str, at):
	row = frappe.db.get_value(doctype, docname, list(DIRECTION_FIELDS.values()), as_dict=True)
	if not row or (row[field] and row[field] >= at):
		return

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
