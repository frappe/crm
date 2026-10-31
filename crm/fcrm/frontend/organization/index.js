// CRM Organization's Deals and Contacts tabs, first on the record's strip.
import { __ } from 'frappe/i18n'
import { readStatuses } from '../status/index.js'
import ContactsTab from './ContactsTab.vue'
import DealsTab from './DealsTab.vue'
import { placeOrganizationTabs } from './organizationTabs.js'

export function addOrganizationTabs(page) {
	placeOrganizationTabs(
		page,
		{
			deals: { label: __('Deals'), component: DealsTab },
			contacts: { label: __('Contacts'), component: ContactsTab },
		},
		readStatuses,
	)
}
