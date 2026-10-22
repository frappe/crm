import frappe

from crm.patches.v1_0.backfill_interaction_timestamps import backfill

WHATSAPP_TIMES = """
	SELECT reference_docname reference_name,
		MAX(CASE WHEN direction = 'Incoming' THEN COALESCE(`timestamp`, creation) END) inbound,
		MAX(CASE WHEN direction = 'Outgoing' THEN COALESCE(`timestamp`, creation) END) outbound
	FROM `tabWA Message`
	WHERE reference_doctype = %(doctype)s AND docstatus = 1 AND IFNULL(reaction, '') = ''
	GROUP BY reference_docname
"""


def execute():
	"""Merge WhatsApp message times into last inbound/outbound and awaiting_reply_since."""
	if frappe.db.table_exists("WA Message"):
		backfill(WHATSAPP_TIMES)
