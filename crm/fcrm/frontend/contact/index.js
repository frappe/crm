// Contact's Deals tab on `/apps/crm`.
import { __ } from 'frappe/i18n'
import { readStatuses } from '../status/index.js'
import DealsTab from './DealsTab.vue'
import { placeDealsTab } from './contactDeals.js'

export function addDealsTab(page) {
	placeDealsTab(page, { label: __('Deals'), component: DealsTab }, readStatuses)
}
