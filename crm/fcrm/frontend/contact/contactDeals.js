// What Contact's Deals tab shows on `/apps/crm`, kept free of the desk's imports so it is unit-tested.

export const LINKED_DEALS = 'crm.api.contact.get_linked_deals'

const DEAL_STATUS = 'CRM Deal Status'

/** Adds the Deals tab first on CRM's strip; `/apps/desk` and a new contact get none. */
export function placeDealsTab(page, tab, readStatuses) {
	if (page.app !== 'crm' || page.isNew) return
	const deals = page.cached('linked-deals', () => readDeals(page))
	const statuses = page.cached(`statuses:${DEAL_STATUS}`, () => readStatuses(DEAL_STATUS))
	page.tabs.add({ name: 'deals', icon: 'lucide-handshake', ...tab, props: { deals, statuses } })
	page.tabs.order(['deals'])
}

/** The contact's deals, or `null` when the read failed: a failed fetch would leave the tab loading. */
function readDeals(page) {
	return page.call(LINKED_DEALS, { contact: page.docname }).catch(() => null)
}
