import { describe, expect, it, vi } from 'vitest'
import {
  REACH_METHODS,
  ReachEditor,
  placeReachPickers,
} from '../../../crm/fcrm/frontend/contact/contactReach.js'

const ReachPicker = { name: 'ReachPicker' }

const MESSAGES = {
  primary: 'Primary updated',
  added: 'Added',
  stale: 'Contact changed while you were editing',
}

function fakePage(overrides = {}) {
  return {
    app: 'crm',
    doctype: 'Contact',
    docname: 'Walk 46019',
    isNew: false,
    perms: { write: 1 },
    fieldAccess: vi.fn(() => 'write'),
    isDirty: false,
    doc: {
      email_id: 'ana@example.com',
      mobile_no: '+91 90000 46019',
      email_ids: [
        { email_id: 'ana@example.com', is_primary: 1 },
        { email_id: 'ana.work@example.com', is_primary: 0 },
        { email_id: 'ana@example.com', is_primary: 0 },
        { email_id: '', is_primary: 0 },
      ],
      phone_nos: [
        { phone: '+91 90000 46019', is_primary_mobile_no: 1 },
        { phone: '+91 90000 46020', is_primary_mobile_no: 0 },
      ],
    },
    fields: { update: vi.fn() },
    toast: { success: vi.fn(), error: vi.fn() },
    save: vi.fn(() => Promise.resolve()),
    call: vi.fn(() => Promise.resolve(true)),
    reload: vi.fn(() => Promise.resolve()),
    ...overrides,
  }
}

describe('placeReachPickers', () => {
  it('makes email and mobile writable pickers on /apps/crm', () => {
    const page = fakePage()
    placeReachPickers(page, ReachPicker)

    const patch = { read_only: false, component: ReachPicker, props: { page } }
    expect(page.fields.update.mock.calls).toEqual([
      ['email_id', patch],
      ['mobile_no', patch],
    ])
    expect(page.fieldAccess.mock.calls).toEqual([['email_ids'], ['phone_nos']])
  })

  it.each([
    ['on /apps/desk', { app: 'frappe' }],
    ['on a new contact', { isNew: true }],
    ['without write on the contact', { perms: { read: 1 } }],
  ])('leaves frappe’s fields alone %s', (_, overrides) => {
    const page = fakePage(overrides)
    placeReachPickers(page, ReachPicker)
    expect(page.fields.update).not.toHaveBeenCalled()
  })

  it('skips a picker whose table this user cannot write', () => {
    const page = fakePage({
      fieldAccess: vi.fn((table) => (table === 'phone_nos' ? 'read' : 'write')),
    })
    placeReachPickers(page, ReachPicker)
    expect(
      page.fields.update.mock.calls.map(([fieldname]) => fieldname),
    ).toEqual(['email_id'])
  })
})

describe('ReachEditor', () => {
  it('offers each of the contact’s values once, in table order', () => {
    const page = fakePage()
    expect(new ReachEditor(page, 'email_id', MESSAGES).values()).toEqual([
      'ana@example.com',
      'ana.work@example.com',
    ])
    expect(new ReachEditor(page, 'mobile_no', MESSAGES).values()).toEqual([
      '+91 90000 46019',
      '+91 90000 46020',
    ])
  })

  it('reads no values from a contact with no rows', () => {
    const page = fakePage({ doc: {} })
    expect(new ReachEditor(page, 'email_id', MESSAGES).values()).toEqual([])
  })

  it('offers to add only a typed value the contact does not have', () => {
    const editor = new ReachEditor(fakePage(), 'email_id', MESSAGES)
    expect(editor.canAdd(' new@example.com ')).toBe(true)
    expect(editor.canAdd('ana.work@example.com')).toBe(false)
    expect(editor.canAdd('   ')).toBe(false)
    expect(editor.canAdd(undefined)).toBe(false)
  })

  it.each([
    ['email_id', 'ana.work@example.com', 'email'],
    ['mobile_no', '+91 90000 46020', 'mobile_no'],
  ])(
    'sets %s’s primary through set_as_primary, re-reads, then toasts',
    async (fieldname, value, field) => {
      const order = []
      const page = fakePage({
        save: vi.fn(() => order.push('save')),
        call: vi.fn(() => order.push('call')),
        reload: vi.fn(() => order.push('reload')),
      })
      const done = await new ReachEditor(page, fieldname, MESSAGES).setPrimary(
        value,
      )
      expect(done).toBe(true)
      expect(page.call).toHaveBeenCalledWith(REACH_METHODS.setPrimary, {
        contact: 'Walk 46019',
        field,
        value,
      })
      expect(order).toEqual(['save', 'call', 'reload'])
      expect(page.toast.success).toHaveBeenCalledWith(MESSAGES.primary)
    },
  )

  it('writes nothing when the chosen value is already the primary', async () => {
    const page = fakePage()
    const done = await new ReachEditor(page, 'email_id', MESSAGES).setPrimary(
      'ana@example.com',
    )
    expect(done).toBe(false)
    expect(page.save).not.toHaveBeenCalled()
    expect(page.call).not.toHaveBeenCalled()
  })

  it.each([
    ['email_id', ' new@example.com ', 'email', 'new@example.com'],
    ['mobile_no', '+91 90000 46021', 'phone', '+91 90000 46021'],
  ])(
    'adds a trimmed %s through create_new',
    async (fieldname, typed, field, value) => {
      const page = fakePage()
      const done = await new ReachEditor(page, fieldname, MESSAGES).add(typed)
      expect(done).toBe(true)
      expect(page.call).toHaveBeenCalledWith(REACH_METHODS.add, {
        contact: 'Walk 46019',
        field,
        value,
      })
      expect(page.reload).toHaveBeenCalled()
      expect(page.toast.success).toHaveBeenCalledWith(MESSAGES.added)
    },
  )

  it('adds nothing the contact already has', async () => {
    const page = fakePage()
    const done = await new ReachEditor(page, 'mobile_no', MESSAGES).add(
      '+91 90000 46020',
    )
    expect(done).toBe(false)
    expect(page.call).not.toHaveBeenCalled()
  })

  it('toasts a refused add and re-reads nothing', async () => {
    const page = fakePage({
      call: vi.fn(() => Promise.reject(new Error('Invalid Email Address'))),
    })
    const done = await new ReachEditor(page, 'email_id', MESSAGES).add('nope')
    expect(done).toBe(false)
    expect(page.toast.error).toHaveBeenCalledWith('Invalid Email Address')
    expect(page.reload).not.toHaveBeenCalled()
  })
})
