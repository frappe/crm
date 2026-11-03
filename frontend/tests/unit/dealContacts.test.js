import { afterEach, describe, expect, it, vi } from 'vitest'
import {
  ContactsEditor,
  callContact,
  canCall,
  canEmail,
  emailContact,
  FIRST_LAYOUT_SECTION,
  dealContacts,
  placeContactsSection,
} from '../../../crm/fcrm/frontend/contacts/dealContacts.js'
import {
  callState,
  registerOutgoingStarter,
} from '../../../crm/fcrm/frontend/telephony/callState.js'

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
    fieldAccess: vi.fn(() => 'write'),
    isDirty: false,
    doc: {
      contacts: [
        { contact: 'Ana Ruiz', full_name: 'Ana Ruiz', is_primary: 0 },
        { contact: 'Ben Okafor', full_name: 'Ben Okafor', is_primary: 1 },
      ],
    },
    panelSections: { add: vi.fn(), has: vi.fn(() => true) },
    create: vi.fn(() => Promise.resolve({ name: 'Dana Walk' })),
    toast: { success: vi.fn(), error: vi.fn() },
    save: vi.fn(() => Promise.resolve()),
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
      { before: 'sla_section' }
    )
    expect(page.panelSections.has).toHaveBeenCalledWith(FIRST_LAYOUT_SECTION)
  })

  it('goes right after the people rows when the layout has no SLA section', () => {
    const page = fakePage({
      panelSections: { add: vi.fn(), has: vi.fn(() => false) },
    })
    placeContactsSection(page, { label: 'Contacts' })
    expect(page.panelSections.add).toHaveBeenCalledWith(
      { name: 'contacts', label: 'Contacts' },
      { after: 'people' }
    )
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

  it('edits only when the contacts table is writable for this user', () => {
    const page = fakePage({ fieldAccess: vi.fn(() => 'read') })
    expect(new ContactsEditor(page, MESSAGES).editable).toBe(false)
    expect(page.fieldAccess).toHaveBeenCalledWith('contacts')
  })

  it('adds a row for the contact to the draft, saves it, then toasts', async () => {
    const page = fakePage()
    const done = await new ContactsEditor(page, MESSAGES).add('Cara Lim')
    expect(done).toBe(true)
    expect(page.doc.contacts.map((row) => row.contact)).toEqual([
      'Ana Ruiz',
      'Ben Okafor',
      'Cara Lim',
    ])
    expect(page.doc.contacts[2]).toEqual({ contact: 'Cara Lim' })
    expect(page.save).toHaveBeenCalledTimes(1)
    expect(page.toast.success).toHaveBeenCalledWith(MESSAGES.added)
  })

  it('removes the contact’s row from the draft, then saves', async () => {
    const page = fakePage()
    await new ContactsEditor(page, MESSAGES).remove('Ana Ruiz')
    expect(page.doc.contacts.map((row) => row.contact)).toEqual(['Ben Okafor'])
    expect(page.save).toHaveBeenCalledTimes(1)
    expect(page.toast.success).toHaveBeenCalledWith(MESSAGES.removed)
  })

  it('marks only the chosen contact primary, then saves', async () => {
    const page = fakePage()
    await new ContactsEditor(page, MESSAGES).setPrimary('Ana Ruiz')
    expect(
      page.doc.contacts.map((row) => [row.contact, row.is_primary])
    ).toEqual([
      ['Ana Ruiz', 1],
      ['Ben Okafor', 0],
    ])
    expect(page.toast.success).toHaveBeenCalledWith(MESSAGES.primary)
  })

  it('saves the draft as the page holds it at save time', async () => {
    const page = fakePage()
    page.save = vi.fn(() => {
      expect(page.doc.contacts.map((row) => row.contact)).toContain('Cara Lim')
      return Promise.resolve()
    })
    await new ContactsEditor(page, MESSAGES).add('Cara Lim')
    expect(page.save).toHaveBeenCalled()
  })

  it('refuses a contact the deal already has, without a save', async () => {
    const page = fakePage()
    const done = await new ContactsEditor(page, MESSAGES).add('Ana Ruiz')
    expect(done).toBe(false)
    expect(page.toast.error).toHaveBeenCalledWith(MESSAGES.duplicate)
    expect(page.save).not.toHaveBeenCalled()
    expect(page.doc.contacts).toHaveLength(2)
  })

  it.each([
    ['add', 'Cara Lim'],
    ['remove', 'Ana Ruiz'],
    ['setPrimary', 'Ana Ruiz'],
  ])(
    'puts the rows back when the save of %s is refused, keeping other edits',
    async (verb, contact) => {
      const page = fakePage({
        save: vi.fn(() => Promise.reject(new Error('Not permitted'))),
      })
      const before = page.doc.contacts
      page.doc.deal_value = 500
      const done = await new ContactsEditor(page, MESSAGES)[verb](contact)
      expect(done).toBe(false)
      expect(page.doc.contacts).toBe(before)
      expect(before.map((row) => [row.contact, row.is_primary])).toEqual([
        ['Ana Ruiz', 0],
        ['Ben Okafor', 1],
      ])
      expect(page.doc.deal_value).toBe(500)
      expect(page.toast.error).toHaveBeenCalledWith('Not permitted')
      expect(page.toast.success).not.toHaveBeenCalled()
    }
  )

  it('leaves a draft that a conflict’s reload replaced as the server sent it', async () => {
    const page = fakePage()
    const reloaded = [
      { contact: 'Eve Tan', full_name: 'Eve Tan', is_primary: 1 },
    ]
    page.save = vi.fn(() => {
      page.doc = { contacts: reloaded }
      return Promise.reject(
        Object.assign(new Error('Changed'), { name: 'SaveConflict' })
      )
    })
    expect(await new ContactsEditor(page, MESSAGES).add('Cara Lim')).toBe(false)
    expect(page.doc.contacts).toBe(reloaded)
    expect(page.toast.error).not.toHaveBeenCalled()
  })

  it('saves a dirty draft first, so the contacts change lands on the saved copy', async () => {
    const page = fakePage({ isDirty: true })
    const sent = []
    page.save = vi.fn(() => {
      sent.push(page.doc.contacts.map((row) => row.contact))
      page.isDirty = false
      return Promise.resolve()
    })
    expect(await new ContactsEditor(page, MESSAGES).add('Cara Lim')).toBe(true)
    expect(sent).toEqual([
      ['Ana Ruiz', 'Ben Okafor'],
      ['Ana Ruiz', 'Ben Okafor', 'Cara Lim'],
    ])
  })

  it('changes no rows when the dirty draft’s own save is refused', async () => {
    const page = fakePage({
      isDirty: true,
      save: vi.fn(() => Promise.reject(new Error('Mandatory'))),
    })
    const before = page.doc.contacts
    expect(await new ContactsEditor(page, MESSAGES).remove('Ana Ruiz')).toBe(
      false
    )
    expect(page.save).toHaveBeenCalledTimes(1)
    expect(page.doc.contacts).toBe(before)
    expect(page.toast.error).toHaveBeenCalledWith('Mandatory')
  })

  it('runs one write at a time and is busy while it runs', async () => {
    let finish
    const page = fakePage({
      save: vi.fn(() => new Promise((resolve) => (finish = resolve))),
    })
    const editor = new ContactsEditor(page, MESSAGES)
    const first = editor.add('Cara Lim')
    expect(editor.busy.value).toBe(true)
    expect(await editor.remove('Ana Ruiz')).toBe(false)
    finish()
    expect(await first).toBe(true)
    expect(editor.busy.value).toBe(false)
    expect(page.save).toHaveBeenCalledTimes(1)
  })

  it('is no longer busy after a refused save', async () => {
    const page = fakePage({
      save: vi.fn(() => Promise.reject(new Error('Refused'))),
    })
    const editor = new ContactsEditor(page, MESSAGES)
    await editor.add('Cara Lim')
    expect(editor.busy.value).toBe(false)
  })

  it('creates a contact in Quick Entry, then adds it to the deal', async () => {
    const page = fakePage()
    const values = { first_name: 'Dana', company_name: 'Acme' }
    const done = await new ContactsEditor(page, MESSAGES).create(values)
    expect(done).toBe(true)
    expect(page.create).toHaveBeenCalledWith('Contact', { values })
    expect(page.doc.contacts.at(-1)).toEqual({ contact: 'Dana Walk' })
    expect(page.save).toHaveBeenCalledTimes(1)
  })

  it('adds nothing when Quick Entry is closed without a save', async () => {
    const page = fakePage({ create: vi.fn(() => Promise.resolve(null)) })
    expect(await new ContactsEditor(page, MESSAGES).create({})).toBe(false)
    expect(page.save).not.toHaveBeenCalled()
  })

  it('toasts a failed Quick Entry and adds nothing', async () => {
    const page = fakePage({
      create: vi.fn(() => Promise.reject(new Error('No permission'))),
    })
    expect(await new ContactsEditor(page, MESSAGES).create({})).toBe(false)
    expect(page.toast.error).toHaveBeenCalledWith('No permission')
    expect(page.save).not.toHaveBeenCalled()
  })
})

describe('a contact’s email and mobile', () => {
  let unregister = () => {}
  afterEach(() => {
    unregister()
    callState.media = []
  })

  it('dials only while the user has a calling medium', () => {
    callState.media = []
    expect(canCall()).toBe(false)
    callState.media = ['Twilio']
    expect(canCall()).toBe(true)
  })

  it('calls the number through the call window', async () => {
    const start = vi.fn(() => Promise.resolve())
    unregister = registerOutgoingStarter(start)
    const page = fakePage()
    await callContact(page, '+1 555 0101')
    expect(start).toHaveBeenCalledWith('+1 555 0101')
    expect(page.toast.error).not.toHaveBeenCalled()
  })

  it('toasts a call window that is still loading', async () => {
    const page = fakePage()
    await callContact(page, '+1 555 0101')
    expect(page.toast.error).toHaveBeenCalledWith(
      expect.stringContaining('still loading')
    )
  })

  it('emails only when the deal offers its email writer', () => {
    const has = vi.fn((name) => name !== 'email')
    expect(canEmail(fakePage({ composer: { has } }))).toBe(false)
    expect(has).toHaveBeenCalledWith('email')
    expect(canEmail(fakePage({ composer: { has: () => true } }))).toBe(true)
  })

  it('opens the deal’s email writer with the contact in To', () => {
    const page = fakePage({ composer: { open: vi.fn() } })
    emailContact(page, 'ana@example.com')
    expect(page.composer.open).toHaveBeenCalledWith('email', {
      draft: { to: ['ana@example.com'] },
    })
  })
})
