import { describe, expect, it, vi } from 'vitest'
import {
  CONTACT_DEALS,
  placeDealsTab,
} from '../../../crm/fcrm/frontend/contact/contactDeals.js'
import { linkedQuery } from '../../../crm/fcrm/frontend/linked/linkedQuery.js'

const DealsTab = { name: 'DealsTab' }
const TAB = { label: 'Deals', component: DealsTab }
const STATUSES = [{ name: 'Won', color: 'green' }]

function fakePage(overrides = {}) {
  return {
    app: 'crm',
    doctype: 'Contact',
    docname: 'Contact 45892',
    isNew: false,
    tabs: { add: vi.fn(), order: vi.fn() },
    cached: vi.fn(() => STATUSES),
    ...overrides,
  }
}

describe('placeDealsTab', () => {
  it('adds the Deals tab first on /apps/crm with the deal statuses', () => {
    const page = fakePage()
    const readStatuses = vi.fn()
    placeDealsTab(page, TAB, readStatuses)

    expect(page.tabs.add).toHaveBeenCalledWith({
      name: 'deals',
      icon: 'lucide-handshake',
      label: 'Deals',
      component: DealsTab,
      props: { statuses: STATUSES },
    })
    expect(page.tabs.order).toHaveBeenCalledWith(['deals'])
    expect(page.cached).toHaveBeenCalledWith(
      'statuses:CRM Deal Status',
      expect.any(Function),
    )
    page.cached.mock.calls[0][1]()
    expect(readStatuses).toHaveBeenCalledWith('CRM Deal Status')
  })

  it.each([
    ['on /apps/desk', { app: 'frappe' }],
    ['on a new contact', { isNew: true }],
  ])('adds no tab and reads nothing %s', (_, overrides) => {
    const page = fakePage(overrides)
    placeDealsTab(page, TAB, vi.fn())

    expect(page.cached).not.toHaveBeenCalled()
    expect(page.tabs.add).not.toHaveBeenCalled()
    expect(page.tabs.order).not.toHaveBeenCalled()
  })
})

describe('CONTACT_DEALS', () => {
  it("lists each CRM Deal once by a contact in the deal's contacts table", () => {
    expect(CONTACT_DEALS.doctype).toBe('CRM Deal')
    expect(linkedQuery(CONTACT_DEALS, 'Contact 45892')).toMatchObject({
      filters: { 'contacts.contact': 'Contact 45892' },
      group_by: 'name',
    })
  })
})
