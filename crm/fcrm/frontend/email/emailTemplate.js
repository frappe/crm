const COPY_OF = '__copy_of'

// CRM v1 copies a template switched off, so a copy goes live only when the admin enables it.
export function startCopyDisabled(page) {
	if (!page.isNew || page.app !== 'crm') return
	if (page.router.currentRoute.value.query[COPY_OF]) page.doc.enabled = 0
}
