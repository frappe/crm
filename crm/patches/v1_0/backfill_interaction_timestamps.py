import frappe

EMAIL_TIMES = """
	SELECT reference_name,
		MAX(CASE WHEN sent_or_received = 'Received' THEN COALESCE(communication_date, creation) END) inbound,
		MAX(CASE WHEN sent_or_received = 'Sent' THEN COALESCE(communication_date, creation) END) outbound
	FROM `tabCommunication`
	WHERE reference_doctype = %(doctype)s AND communication_type = 'Communication'
	GROUP BY reference_name
"""


def execute():
	backfill(EMAIL_TIMES)


def backfill(times_query: str):
	"""`times_query` takes a %(doctype)s parameter and returns reference_name, inbound and outbound."""
	for doctype in ("CRM Lead", "CRM Deal"):
		merge_times(doctype, times_query)
	forward_converted_leads()
	for doctype in ("CRM Lead", "CRM Deal"):
		set_awaiting_reply_since(doctype)


def merge_times(doctype: str, times_query: str):
	frappe.db.sql(
		f"""
		UPDATE `tab{doctype}` record
		JOIN ({times_query}) times ON times.reference_name = record.name
		SET
			record.last_inbound_at = {latest("record.last_inbound_at", "times.inbound")},
			record.last_outbound_at = {latest("record.last_outbound_at", "times.outbound")}
		""",
		{"doctype": doctype},
	)


def forward_converted_leads():
	frappe.db.sql(
		f"""
		UPDATE `tabCRM Deal` deal
		JOIN (
			SELECT `lead`, MAX(creation) creation FROM `tabCRM Deal`
			WHERE IFNULL(`lead`, '') != '' GROUP BY `lead`
		) latest ON latest.`lead` = deal.`lead` AND latest.creation = deal.creation
		JOIN `tabCRM Lead` lead_record ON lead_record.name = deal.`lead` AND lead_record.converted = 1
		SET
			deal.last_inbound_at = {latest("deal.last_inbound_at", "lead_record.last_inbound_at")},
			deal.last_outbound_at = {latest("deal.last_outbound_at", "lead_record.last_outbound_at")}
		"""
	)


def set_awaiting_reply_since(doctype: str):
	frappe.db.sql(
		f"""
		UPDATE `tab{doctype}`
		SET awaiting_reply_since = CASE
			WHEN last_inbound_at IS NOT NULL AND (last_outbound_at IS NULL OR last_inbound_at > last_outbound_at)
			THEN last_inbound_at
		END
		"""
	)


def latest(a: str, b: str) -> str:
	# GREATEST is NULL when any argument is NULL, hence the COALESCE pairs.
	return f"GREATEST(COALESCE({a}, {b}), COALESCE({b}, {a}))"
