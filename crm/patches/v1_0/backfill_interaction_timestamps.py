import frappe


def execute():
	"""Backfill last inbound/outbound email times and awaiting_reply_since on leads and deals."""
	for doctype in ("CRM Lead", "CRM Deal"):
		set_from_emails(doctype)
	forward_converted_leads()
	for doctype in ("CRM Lead", "CRM Deal"):
		set_awaiting_reply_since(doctype)


def set_from_emails(doctype: str):
	frappe.db.sql(
		f"""
		UPDATE `tab{doctype}` record
		JOIN (
			SELECT reference_name,
				MAX(CASE WHEN sent_or_received = 'Received' THEN COALESCE(communication_date, creation) END) inbound,
				MAX(CASE WHEN sent_or_received = 'Sent' THEN COALESCE(communication_date, creation) END) outbound
			FROM `tabCommunication`
			WHERE reference_doctype = %(doctype)s AND communication_type = 'Communication'
			GROUP BY reference_name
		) email ON email.reference_name = record.name
		SET record.last_inbound_at = email.inbound, record.last_outbound_at = email.outbound
		""",
		{"doctype": doctype},
	)


def forward_converted_leads():
	# GREATEST is NULL when any argument is NULL, hence the COALESCE pairs.
	frappe.db.sql(
		"""
		UPDATE `tabCRM Deal` deal
		JOIN (
			SELECT `lead`, MAX(creation) creation FROM `tabCRM Deal`
			WHERE IFNULL(`lead`, '') != '' GROUP BY `lead`
		) latest ON latest.`lead` = deal.`lead` AND latest.creation = deal.creation
		JOIN `tabCRM Lead` lead_record ON lead_record.name = deal.`lead` AND lead_record.converted = 1
		SET
			deal.last_inbound_at = GREATEST(
				COALESCE(deal.last_inbound_at, lead_record.last_inbound_at),
				COALESCE(lead_record.last_inbound_at, deal.last_inbound_at)
			),
			deal.last_outbound_at = GREATEST(
				COALESCE(deal.last_outbound_at, lead_record.last_outbound_at),
				COALESCE(lead_record.last_outbound_at, deal.last_outbound_at)
			)
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
