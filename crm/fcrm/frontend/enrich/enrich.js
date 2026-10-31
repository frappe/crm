// What the header's Enrich entry does, kept free of the desk's imports so it is unit-tested.
export const ENRICH_METHOD = 'crm.domain_enrichment.api.enrich'
export const ENRICHABLE_METHOD = 'crm.domain_enrichment.api.enrichable_doctypes'

/** Adds the entry to `⋯` once the visit's read shows enrichment is set up for this doctype. */
export function placeEnrichItem(page, item) {
	if (page.isNew) return
	const enrichable = page.cached('enrichable_doctypes', () => page.call(ENRICHABLE_METHOD))
	if (!enrichable?.includes(page.doctype)) return
	page.header.add({ name: 'enrich', icon: 'lucide-zap', right: 'write', ...item })
}

/** Queues the record's enrichment; the host toasts a refusal, such as a record with no website. */
export async function enrichRecord(page, startedMessage) {
	await page.call(ENRICH_METHOD, { reference_doctype: page.doctype, reference_name: page.docname })
	page.toast.success(startedMessage)
}
