import { describe, expect, it, vi } from 'vitest'
import {
  CONTACT_METHODS,
  ContactsEditor,
  FIRST_LAYOUT_SECTION,
  dealContacts,
  placeContactsSection,
} from '../../../crm/fcrm/frontend/contacts/dealContacts.js'

const MESSAGES = {
  duplicate: 'Contact already added',
  added: 'Contact added',
  removed: 'Contact removed',
  primary: 'Primary contact set',
}

function fakePage(overrides = {}) {
  return {
    doctype: 'CRM Deal',
    docname: 'CRM-DEAL-45886',
    isNew: false,
    perms: { write: 1 },
    doc: {
      contacts: [
        { contact: 'Ana Ruiz', full_name: 'Ana Ruiz', is_primary: 0 },
        { contact: 'Ben Okafor', full_name: 'Ben Okafor', is_primary: 1 },
      ],
    },
    panelSections: { add: vi.fn() },
    toast: { success: vi.fn(), error: vi.fn() },
    save: vi.fn(() => Promise.resolve()),
    call: vi.fn(() => Promise.resolve(true)),
    reload: vi.fn(() => Promise.resolve()),
    ...overrides,
  }
}

describe('placeContactsSection', () => {
  it('adds the section before the Side Panel layout’s first section', () => {
    const page = fakePage()
    const component = {}
    placeContactsSection(page, { label: 'Contacts', component })
    expect(page.panelSections.add).toHaveBeenCalledWith(
      { name: 'contacts', label: 'Contacts', component },
      { before: FIRST_LAYOUT_SECTION },
    )
    expect(FIRST_LAYOUT_SECTION).toBe('sla_section')
  })

  it('adds nothing on a new deal', () => {
    const page = fakePage({ isNew: true })
    placeContactsSection(page, { label: 'Contacts' })
    expect(page.panelSections.add).not.toHaveBeenCalled()
  })
})

describe('dealContacts', () => {
  it('lists the primary contact first, the rest in table order', () => {
    const doc = {
      contacts: [
        { contact: 'A', is_primary: 0 },
        { contact: 'B', is_primary: 0 },
        { contact: 'C', is_primary: 1 },
        { contact: 'D', is_primary: 0 },
      ],
    }
    expect(dealContacts(doc).map((row) => row.contact)).toEqual([
      'C',
      'A',
      'B',
      'D',
    ])
  })

  it('skips a row with no contact and leaves the doc’s table as it was', () => {
    const doc = { contacts: [{ contact: '' }, { contact: 'A', is_primary: 1 }] }
    expect(dealContacts(doc).map((row) => row.contact)).toEqual(['A'])
    expect(doc.contacts.map((row) => row.contact)).toEqual(['', 'A'])
  })

  it('reads an empty list from a deal with no contacts table', () => {
    expect(dealContacts({})).toEqual([])
    expect(dealContacts(null)).toEqual([])
  })
})

describe('ContactsEditor', () => {
  it('edits only with write on the deal', () => {
    expect(new ContactsEditor(fakePage(), MESSAGES).editable).toBe(true)
    const readOnly = fakePage({ perms: { read: 1 } })
    expect(new ContactsEditor(readOnly, MESSAGES).editable).toBe(false)
  })

  it.each([
    ['add', 'Cara Lim', CONTACT_METHODS.add, MESSAGES.added],
    ['remove', 'Ana Ruiz', CONTACT_METHODS.remove, MESSAGES.removed],
    ['setPrimary', 'Ana Ruiz', CONTACT_METHODS.setPrimary, MESSAGES.primary],
  ])(
    '%s calls its deal method with the contact, re-reads the page, then toasts',
    async (verb, contact, method, message) => {
      const order = []
      const page = fakePage({
        save: vi.fn(() => order.push('save')),
        call: vi.fn(() => order.push('call')),
        reload: vi.fn(() => order.push('reload')),
      })
      const done = await new ContactsEditor(page, MESSAGES)[verb](contact)
      expect(done).toBe(true)
      expect(page.call).toHaveBeenCalledWith(method, {
        deal: 'CRM-DEAL-45886',
        contact,
      })
      expect(order).toEqual(['save', 'call', 'reload'])
      expect(page.toast.success).toHaveBeenCalledWith(message)
    },
  )

  it('names the whitelisted crm_deal methods', () => {
    expect(CONTACT_METHODS).toEqual({
      add: 'crm.fcrm.doctype.crm_deal.crm_deal.add_contact',
      remove: 'crm.fcrm.doctype.crm_deal.crm_deal.remove_contact',
      setPrimary: 'crm.fcrm.doctype.crm_deal.crm_deal.set_primary_contact',
    })
  })

  it('refuses a contact the deal already has, without a call', async () => {
    const page = fakePage()
    const done = await new ContactsEditor(page, MESSAGES).add('Ana Ruiz')
    expect(done).toBe(false)
    expect(page.toast.error).toHaveBeenCalledWith(MESSAGES.duplicate)
    expect(page.save).not.toHaveBeenCalled()
    expect(page.call).not.toHaveBeenCalled()
  })

  it('calls nothing when the draft’s save is refused, and keeps the draft', async () => {
    const page = fakePage({
      save: vi.fn(() => Promise.reject(new Error('Probability must be 0-100'))),
    })
    const done = await new ContactsEditor(page, MESSAGES).remove('Ana Ruiz')
    expect(done).toBe(false)
    expect(page.toast.error).toHaveBeenCalledWith('Probability must be 0-100')
    expect(page.call).not.toHaveBeenCalled()
    expect(page.reload).not.toHaveBeenCalled()
  })

  it('toasts a refused call and re-reads nothing', async () => {
    const page = fakePage({
      call: vi.fn(() =>
        Promise.reject(new Error('Not allowed to add contact to Deal')),
      ),
    })
    const done = await new ContactsEditor(page, MESSAGES).add('Cara Lim')
    expect(done).toBe(false)
    expect(page.toast.error).toHaveBeenCalledWith(
      'Not allowed to add contact to Deal',
    )
    expect(page.reload).not.toHaveBeenCalled()
    expect(page.toast.success).not.toHaveBeenCalled()
  })
})
