const LEAD = 'CRM Lead'

// CRM's first sync reads the whole inbox, 100 mails at a time.
export function startNewAccount(page) {
	if (!page.isNew || page.app !== 'crm') return
	if (!page.doc.imap_folder?.length)
		page.doc.imap_folder = [{ folder_name: 'INBOX' }]
	page.doc.email_sync_option = 'ALL'
	page.doc.initial_sync_count = '100'
	appendToLead(page)
}

// Only an empty Append To is filled, so a doctype the admin picked stays.
export function appendToLead(page) {
	if (page.app !== 'crm') return
	if (!page.doc.use_imap) {
		if (!page.doc.append_to) page.doc.append_to = LEAD
		return
	}
	for (const row of page.doc.imap_folder ?? [])
		if (!row.append_to) row.append_to = LEAD
}
