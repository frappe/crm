import { describe, expect, it, vi } from 'vitest'

const getMeta = vi.fn()
const runDocumentMethod = vi.fn()

vi.mock('@framework/ui/api', () => ({ getMeta, runDocumentMethod }))

const {
  addMappingOptions,
  addRetryAct,
  addSourceActs,
  clearFormOnPageChange,
  mappableFields,
} = await import('../../../crm/fcrm/frontend/lead_sync/leadSync.js')

const routeFor = vi.fn((doctype, name, options) => ({ doctype, name, options }))

function fakePage(doc = {}, overrides = {}) {
  return {
    doctype: 'Lead Sync Source',
    docname: 'LSS 45961',
    isNew: false,
    doc: { type: 'Facebook', facebook_page: 'PAGE-1', ...doc },
    fields: { hide: vi.fn(), update: vi.fn() },
    header: { add: vi.fn() },
    router: {
      resolve: vi.fn(() => ({
        fullPath: '/failed-lead-sync-log?source=LSS 45961',
      })),
    },
    toast: { success: vi.fn(), error: vi.fn() },
    save: vi.fn().mockResolvedValue(true),
    refresh: vi.fn().mockResolvedValue(),
    cached: vi.fn(() => undefined),
    ...overrides,
  }
}

function acts(page) {
  return Object.fromEntries(
    page.header.add.mock.calls[0][0].map((act) => [act.name, act]),
  )
}

describe('a new lead sync source', () => {
  it('hides the page and the form until the first save has fetched them', () => {
    const page = fakePage({}, { isNew: true })
    addSourceActs(page, routeFor)

    expect(page.fields.hide.mock.calls).toEqual([
      ['facebook_page'],
      ['facebook_lead_form'],
    ])
    expect(page.header.add).not.toHaveBeenCalled()
  })
})

describe('a saved lead sync source', () => {
  it('offers only the forms of its page', () => {
    const page = fakePage()
    addSourceActs(page, routeFor)

    expect(page.fields.hide).not.toHaveBeenCalled()
    expect(page.fields.update).toHaveBeenCalledWith('facebook_lead_form', {
      link_filters: { page: 'PAGE-1' },
    })
  })

  it('links to the failed syncs of the source', () => {
    const page = fakePage()
    addSourceActs(page, routeFor)

    expect(routeFor).toHaveBeenCalledWith('Failed Lead Sync Log', null, {
      query: { source: 'LSS 45961' },
    })
    expect(acts(page).failed_syncs.href).toBe(
      '/failed-lead-sync-log?source=LSS 45961',
    )
  })

  it('clears the form when the page changes', () => {
    const page = fakePage({
      facebook_page: 'PAGE-2',
      facebook_lead_form: 'FORM-1',
    })
    clearFormOnPageChange(page)

    expect(page.doc.facebook_lead_form).toBe('')
    expect(page.fields.update).toHaveBeenCalledWith('facebook_lead_form', {
      link_filters: { page: 'PAGE-2' },
    })
  })

  it('leaves the form of a new source alone', () => {
    const page = fakePage({ facebook_lead_form: 'FORM-1' }, { isNew: true })
    clearFormOnPageChange(page)

    expect(page.doc.facebook_lead_form).toBe('FORM-1')
  })

  it('syncs the saved source on Sync Now', async () => {
    runDocumentMethod.mockResolvedValueOnce({ data: null })
    const page = fakePage()
    addSourceActs(page, routeFor)
    await acts(page).sync_now.run(page)

    expect(page.save).toHaveBeenCalled()
    expect(runDocumentMethod).toHaveBeenCalledWith(
      'Lead Sync Source',
      'LSS 45961',
      'sync_leads',
      {},
      { nullable: true },
    )
    expect(page.toast.success).toHaveBeenCalled()
  })

  it('shows the failure of the sync', async () => {
    runDocumentMethod.mockRejectedValueOnce(
      new Error('Please check your access token'),
    )
    const page = fakePage()
    addSourceActs(page, routeFor)
    await acts(page).sync_now.run(page)

    expect(page.toast.error).toHaveBeenCalledWith(
      'Please check your access token',
    )
    expect(page.toast.success).not.toHaveBeenCalled()
  })

  it('does not sync when the save is refused', async () => {
    runDocumentMethod.mockClear()
    const page = fakePage(
      {},
      { save: vi.fn().mockResolvedValue(false) },
    )
    addSourceActs(page, routeFor)
    await acts(page).sync_now.run(page)

    expect(runDocumentMethod).not.toHaveBeenCalled()
    expect(page.toast.error).not.toHaveBeenCalled()
  })
})

describe('the field mapping', () => {
  it('waits for the CRM Lead fields before it sets the picker', () => {
    const page = fakePage({}, { doctype: 'Facebook Lead Form' })

    expect(addMappingOptions(page)).toBeUndefined()
    expect(page.cached.mock.calls[0][0]).toBe('lead_sync:crm_lead_fields')
    expect(page.fields.update).not.toHaveBeenCalled()
  })

  it('lists the CRM Lead fields a question may fill, by label', async () => {
    getMeta.mockResolvedValueOnce({
      data: {
        fields: [
          { fieldname: 'first_name', label: 'First Name', fieldtype: 'Data' },
          {
            fieldname: 'section_1',
            label: 'Details',
            fieldtype: 'Section Break',
          },
          {
            fieldname: 'creation_note',
            label: 'Note',
            fieldtype: 'Text',
            read_only: 1,
          },
          { fieldname: 'status', label: 'Status', fieldtype: 'Link' },
        ],
      },
    })
    const page = fakePage(
      {},
      { doctype: 'Facebook Lead Form', cached: vi.fn() },
    )
    addMappingOptions(page)
    const fields = await page.cached.mock.calls[0][1]()
    page.cached.mockReturnValue(fields)
    addMappingOptions(page)

    expect(page.fields.update).toHaveBeenCalledWith(
      'questions.mapped_to_crm_field',
      {
        options: [
          { value: 'first_name', label: 'First Name' },
          { value: 'status', label: 'Status' },
        ],
        placeholder: 'Not Synced',
      },
    )
  })

  it('names a field with no label by its fieldname', () => {
    expect(mappableFields([{ fieldname: 'email', fieldtype: 'Data' }])).toEqual(
      [{ value: 'email', label: 'email' }],
    )
  })
})

describe('a failed sync log', () => {
  const log = (type, overrides) =>
    fakePage(
      { type },
      { doctype: 'Failed Lead Sync Log', docname: 'LOG-1', ...overrides },
    )

  it.each(['Failure', 'Duplicate'])('offers Retry Sync for a %s', (type) => {
    const page = log(type)
    addRetryAct(page)

    expect(page.header.add.mock.calls[0][0].name).toBe('retry_sync')
  })

  it('offers nothing once the log is Synced', () => {
    const page = log('Synced')
    addRetryAct(page)

    expect(page.header.add).not.toHaveBeenCalled()
  })

  it('retries the log and reloads it', async () => {
    runDocumentMethod.mockResolvedValueOnce({ data: { name: 'LEAD-1' } })
    const page = log('Failure')
    addRetryAct(page)
    await page.header.add.mock.calls[0][0].run(page)

    expect(runDocumentMethod).toHaveBeenCalledWith(
      'Failed Lead Sync Log',
      'LOG-1',
      'retry_sync',
    )
    expect(page.toast.success).toHaveBeenCalledWith(
      'Sync successful, CRM Lead: LEAD-1',
    )
    expect(page.refresh).toHaveBeenCalled()
  })

  it('shows the server refusal and keeps the log', async () => {
    runDocumentMethod.mockRejectedValueOnce(new Error('Token expired'))
    const page = log('Failure')
    addRetryAct(page)
    await page.header.add.mock.calls[0][0].run(page)

    expect(page.toast.error).toHaveBeenCalledWith('Token expired')
    expect(page.refresh).not.toHaveBeenCalled()
  })
})
