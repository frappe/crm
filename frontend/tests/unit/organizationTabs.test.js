import { describe, expect, it, vi } from 'vitest'
import {
  CONTACT_FIELDS,
  DEAL_FIELDS,
  linkedQuery,
  placeOrganizationTabs,
} from '../../../crm/fcrm/frontend/organization/organizationTabs.js'

const DealsTab = { name: 'DealsTab' }
const ContactsTab = { name: 'ContactsTab' }
const TABS = {
  deals: { label: 'Deals', component: DealsTab },
  contacts: { label: 'Contacts', component: ContactsTab },
}
const STATUSES = [{ name: 'Won', color: 'green' }]

function fakePage(overrides = {}) {
  return {
    doctype: 'CRM Organization',
    docname: 'Org 45891',
    isNew: false,
    tabs: { add: vi.fn(), order: vi.fn() },
    cached: vi.fn(() => STATUSES),
    ...overrides,
  }
}

describe('placeOrganizationTabs', () => {
  it('adds Deals with the deal statuses and Contacts, then puts them first', () => {
    const page = fakePage()
    const readStatuses = vi.fn()
    placeOrganizationTabs(page, TABS, readStatuses)

    expect(page.cached).toHaveBeenCalledWith(
      'statuses:CRM Deal Status',
      expect.any(Function),
    )
    page.cached.mock.calls[0][1]()
    expect(readStatuses).toHaveBeenCalledWith('CRM Deal Status')
    expect(page.tabs.add.mock.calls).toEqual([
      [
        {
          name: 'deals',
          icon: 'lucide-handshake',
          label: 'Deals',
          component: DealsTab,
          props: { statuses: STATUSES },
        },
      ],
      [
        {
          name: 'contacts',
          icon: 'lucide-contact',
          label: 'Contacts',
          component: ContactsTab,
        },
      ],
    ])
    expect(page.tabs.order).toHaveBeenCalledWith(['deals', 'contacts'])
  })

  it('adds no tab and reads nothing on a new organization', () => {
    const page = fakePage({ isNew: true })
    placeOrganizationTabs(page, TABS, vi.fn())
    expect(page.cached).not.toHaveBeenCalled()
    expect(page.tabs.add).not.toHaveBeenCalled()
    expect(page.tabs.order).not.toHaveBeenCalled()
  })
})

describe('linkedQuery', () => {
  it("filters deals on the deal's organization, newest change first", () => {
    expect(linkedQuery(DEAL_FIELDS, 'organization', 'Org 45891')).toEqual({
      fields: DEAL_FIELDS,
      filters: { organization: 'Org 45891' },
      order_by: 'modified desc',
    })
  })

  it("filters contacts on the contact's company", () => {
    expect(
      linkedQuery(CONTACT_FIELDS, 'company_name', 'Org 45891').filters,
    ).toEqual({
      company_name: 'Org 45891',
    })
  })
})
