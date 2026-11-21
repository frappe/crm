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
	rows = frappe.db.sql(  # only constants are formatted in; doctype is a bound parameter  # nosemgrep
		f"""
		SELECT record.name,
			{latest("record.last_inbound_at", "times.inbound")} last_inbound_at,
			{latest("record.last_outbound_at", "times.outbound")} last_outbound_at
		FROM `tab{doctype}` record
		JOIN ({times_query}) times ON times.reference_name = record.name
		""",
		{"doctype": doctype},
		as_dict=True,
	)
	write_times(doctype, rows)


def forward_converted_leads():
	rows = frappe.db.sql(  # only constants are formatted in  # nosemgrep
		f"""
		SELECT deal.name,
			{latest("deal.last_inbound_at", "lead_record.last_inbound_at")} last_inbound_at,
			{latest("deal.last_outbound_at", "lead_record.last_outbound_at")} last_outbound_at
		FROM `tabCRM Deal` deal
		JOIN (
			SELECT `lead`, MAX(creation) creation FROM `tabCRM Deal`
			WHERE IFNULL(`lead`, '') != '' GROUP BY `lead`
		) latest ON latest.`lead` = deal.`lead` AND latest.creation = deal.creation
		JOIN `tabCRM Lead` lead_record ON lead_record.name = deal.`lead` AND lead_record.converted = 1
		""",
		as_dict=True,
	)
	write_times("CRM Deal", rows)


def write_times(doctype: str, rows: list):
	"""Update through `bulk_update`, as a multi-table UPDATE does not run on SQLite."""
	frappe.db.bulk_update(
		doctype,
		{
			row.name: {"last_inbound_at": row.last_inbound_at, "last_outbound_at": row.last_outbound_at}
			for row in rows
		},
		update_modified=False,
	)


def set_awaiting_reply_since(doctype: str):
	frappe.db.sql(  # doctype is CRM Lead or CRM Deal, set by the patch  # nosemgrep
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
