// What Contact's Deals tab shows on `/apps/crm`, kept free of the desk's imports so it is unit-tested.

export const CONTACT_DEALS = {
	doctype: 'CRM Deal',
	field: 'contacts.contact',
	fields: [
		'name',
		'organization',
		'organization.organization_logo as organization_logo',
		'status',
		'deal_value',
		'currency',
		'email',
		'mobile_no',
		'deal_owner',
		'deal_owner.full_name as deal_owner_name',
		'modified',
	],
}

const DEAL_STATUS = 'CRM Deal Status'

/** Adds the Deals tab first on CRM's strip; `/apps/desk` and a new contact get none. */
export function placeDealsTab(page, tab, readStatuses) {
	if (page.app !== 'crm' || page.isNew) return
	const statuses = page.cached(`statuses:${DEAL_STATUS}`, () => readStatuses(DEAL_STATUS))
	page.tabs.add({ name: 'deals', icon: 'lucide-handshake', ...tab, props: { statuses } })
	page.tabs.order(['deals'])
}
