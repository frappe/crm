// What CRM Organization's Deals and Contacts tabs list, kept free of the desk's imports so it is unit-tested.
import { STATUS_DOCTYPES } from '../status/statusChange.js'

export const DEALS = {
	doctype: 'CRM Deal',
	field: 'organization',
	fields: ['name', 'status', 'deal_value', 'currency', 'deal_owner.full_name as deal_owner_name', 'modified'],
}

export const CONTACTS = {
	doctype: 'Contact',
	field: 'company_name',
	fields: ['name', 'full_name', 'image', 'email_id', 'mobile_no', 'modified'],
}

/** Adds the Deals and Contacts tabs first on the strip; a new organization has neither yet. */
export function placeOrganizationTabs(page, tabs, readStatuses) {
	if (page.isNew) return
	const statusDoctype = STATUS_DOCTYPES['CRM Deal']
	const statuses = page.cached(`statuses:${statusDoctype}`, () => readStatuses(statusDoctype))
	page.tabs.add({ name: 'deals', icon: 'lucide-handshake', ...tabs.deals, props: { statuses } })
	page.tabs.add({ name: 'contacts', icon: 'lucide-contact', ...tabs.contacts })
	page.tabs.order(['deals', 'contacts'])
}

/** The list query for `source`'s rows that name the organization, newest change first. */
export function linkedQuery(source, organization) {
	return { fields: source.fields, filters: { [source.field]: organization }, order_by: 'modified desc' }
}
