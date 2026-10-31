// What CRM Organization's Deals and Contacts tabs list, kept free of the desk's imports so it is unit-tested.

const DEAL_STATUS = 'CRM Deal Status'

export const DEAL_FIELDS = [
	'name',
	'status',
	'deal_value',
	'currency',
	'deal_owner.full_name as deal_owner_name',
	'modified',
]

export const CONTACT_FIELDS = ['name', 'full_name', 'image', 'email_id', 'mobile_no', 'modified']

/** Adds the Deals and Contacts tabs first on the strip; a new organization has neither yet. */
export function placeOrganizationTabs(page, tabs, readStatuses) {
	if (page.isNew) return
	const statuses = page.cached(`statuses:${DEAL_STATUS}`, () => readStatuses(DEAL_STATUS))
	page.tabs.add({ name: 'deals', icon: 'lucide-handshake', ...tabs.deals, props: { statuses } })
	page.tabs.add({ name: 'contacts', icon: 'lucide-contact', ...tabs.contacts })
	page.tabs.order(['deals', 'contacts'])
}

/** The list query for `doctype`'s rows whose `field` names the organization, newest change first. */
export function linkedQuery(fields, field, organization) {
	return { fields, filters: { [field]: organization }, order_by: 'modified desc' }
}
