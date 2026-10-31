// The Enrich entry on CRM Lead's, Deal's and Organization's record pages: `header.enrich`, in `⋯`.
import { __ } from 'frappe/i18n'
import { enrichRecord, placeEnrichItem } from './enrich.js'

export function addEnrichItem(page) {
	placeEnrichItem(page, {
		get label() {
			return __('Enrich from website')
		},
		run: (page) => enrichRecord(page, __('Enrichment started. Reload the page to see the result.')),
	})
}
