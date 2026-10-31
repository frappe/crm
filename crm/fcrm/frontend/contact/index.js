// Contact's Deals tab and email and mobile pickers on `/apps/crm`.
import { __ } from 'frappe/i18n'
import { readStatuses } from '../status/index.js'
import DealsTab from './DealsTab.vue'
import ReachPicker from './ReachPicker.vue'
import { placeDealsTab } from './contactDeals.js'
import { placeReachPickers } from './contactReach.js'

export function addDealsTab(page) {
	placeDealsTab(page, { label: __('Deals'), component: DealsTab }, readStatuses)
}

export function addReachPickers(page) {
	placeReachPickers(page, ReachPicker)
}
