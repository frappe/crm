// A CRM Form Script's v1 calls, as a panel section on its record page.
import { __ } from 'frappe/i18n'
import V1Calls from './V1Calls.vue'
import { placeCallsSection } from './v1Calls.js'

export function addCallsSection(page) {
	placeCallsSection(page, { label: __('V1 Calls'), component: V1Calls })
}
