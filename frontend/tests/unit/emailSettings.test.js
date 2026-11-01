import { describe, expect, it } from 'vitest'
import {
  appendToLead,
  startCopyDisabled,
  startNewAccount,
} from '../../../crm/fcrm/frontend/email/index.js'

function fakePage(doc = {}, overrides = {}) {
  return { isNew: true, app: 'crm', doc: { ...doc }, ...overrides }
}

describe('a new email account', () => {
  it('syncs the whole inbox into CRM Lead', () => {
    const page = fakePage({ use_imap: 1 })
    startNewAccount(page)

    expect(page.doc.imap_folder).toEqual([
      { folder_name: 'INBOX', append_to: 'CRM Lead' },
    ])
    expect(page.doc.email_sync_option).toBe('ALL')
    expect(page.doc.initial_sync_count).toBe('100')
  })

  it('fills the folder row that desk already added', () => {
    const page = fakePage({
      use_imap: 1,
      imap_folder: [{ folder_name: 'INBOX' }],
    })
    startNewAccount(page)

    expect(page.doc.imap_folder).toEqual([
      { folder_name: 'INBOX', append_to: 'CRM Lead' },
    ])
  })

  it('leaves a saved account and a page outside CRM alone', () => {
    const saved = fakePage({}, { isNew: false })
    startNewAccount(saved)
    const desk = fakePage({}, { app: 'frappe' })
    startNewAccount(desk)

    expect(saved.doc).toEqual({})
    expect(desk.doc).toEqual({})
  })
})

describe('append to', () => {
  it('fills the account-level field when the account is not IMAP', () => {
    const page = fakePage({ use_imap: 0 })
    appendToLead(page)
    expect(page.doc.append_to).toBe('CRM Lead')
  })

  it('keeps a doctype the admin picked', () => {
    const page = fakePage({
      use_imap: 1,
      imap_folder: [
        { folder_name: 'INBOX', append_to: 'Issue' },
        { folder_name: 'Sales' },
      ],
    })
    appendToLead(page)

    expect(page.doc.imap_folder.map((row) => row.append_to)).toEqual([
      'Issue',
      'CRM Lead',
    ])
  })

  it('does nothing outside CRM', () => {
    const page = fakePage({ use_imap: 0 }, { app: 'frappe' })
    appendToLead(page)
    expect(page.doc.append_to).toBeUndefined()
  })
})

describe('a copied email template', () => {
  const route = (query) => ({ router: { currentRoute: { value: { query } } } })

  it('starts disabled', () => {
    const page = fakePage({ enabled: 1 }, route({ __copy_of: 'Welcome 45960' }))
    startCopyDisabled(page)
    expect(page.doc.enabled).toBe(0)
  })

  it('keeps a plain new template as it is', () => {
    const page = fakePage({ enabled: 1 }, route({}))
    startCopyDisabled(page)
    expect(page.doc.enabled).toBe(1)
  })

  it('does nothing outside CRM', () => {
    const page = fakePage(
      { enabled: 1 },
      { app: 'frappe', ...route({ __copy_of: 'Welcome 45960' }) },
    )
    startCopyDisabled(page)
    expect(page.doc.enabled).toBe(1)
  })
})
