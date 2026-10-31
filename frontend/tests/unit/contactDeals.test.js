import { describe, expect, it, vi } from 'vitest'
import {
  LINKED_DEALS,
  placeDealsTab,
} from '../../../crm/fcrm/frontend/contact/contactDeals.js'

const DealsTab = { name: 'DealsTab' }
const TAB = { label: 'Deals', component: DealsTab }
const DEALS = [{ name: 'CRM-DEAL-45892' }]
const STATUSES = [{ name: 'Won', color: 'green' }]

function fakePage(overrides = {}) {
  const values = { 'linked-deals': DEALS, 'statuses:CRM Deal Status': STATUSES }
  return {
    app: 'crm',
    doctype: 'Contact',
    docname: 'Contact 45892',
    isNew: false,
    tabs: { add: vi.fn(), order: vi.fn() },
    cached: vi.fn((key) => values[key]),
    call: vi.fn(() => Promise.resolve(DEALS)),
    ...overrides,
  }
}

function fetcher(page, key) {
  return page.cached.mock.calls.find(([name]) => name === key)[1]
}

describe('placeDealsTab', () => {
  it('adds the Deals tab first on /apps/crm with the deals and their statuses', () => {
    const page = fakePage()
    placeDealsTab(page, TAB, vi.fn())

    expect(page.tabs.add).toHaveBeenCalledWith({
      name: 'deals',
      icon: 'lucide-handshake',
      label: 'Deals',
      component: DealsTab,
      props: { deals: DEALS, statuses: STATUSES },
    })
    expect(page.tabs.order).toHaveBeenCalledWith(['deals'])
  })

  it("reads the contact's deals and the deal statuses", async () => {
    const page = fakePage()
    const readStatuses = vi.fn()
    placeDealsTab(page, TAB, readStatuses)

    await expect(fetcher(page, 'linked-deals')()).resolves.toBe(DEALS)
    expect(page.call).toHaveBeenCalledWith(LINKED_DEALS, {
      contact: 'Contact 45892',
    })
    fetcher(page, 'statuses:CRM Deal Status')()
    expect(readStatuses).toHaveBeenCalledWith('CRM Deal Status')
  })

  it('holds null when the deals cannot be read', async () => {
    const page = fakePage({
      call: vi.fn(() => Promise.reject(new Error('Not permitted'))),
    })
    placeDealsTab(page, TAB, vi.fn())

    await expect(fetcher(page, 'linked-deals')()).resolves.toBeNull()
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
