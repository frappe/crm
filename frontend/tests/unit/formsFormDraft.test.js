import { beforeEach, describe, expect, it, vi } from 'vitest'

const api = vi.hoisted(() => ({
  call: vi.fn(),
  toast: { success: vi.fn(), error: vi.fn(), info: vi.fn() },
}))
vi.mock('frappe-ui', async (importOriginal) => ({
  ...(await importOriginal()),
  toast: api.toast,
}))
vi.mock('../../../crm/fcrm/frontend/forms/formsApi.js', () => ({
  call: api.call,
  errorText: (e, fallback) => e?.messages?.[0] || e?.message || fallback,
  recordNames: vi.fn(async () => []),
}))

import { useFormDraft } from '../../../crm/fcrm/frontend/forms/builder/useFormDraft.js'

const SERVER_FORM = {
  title: 'Contact us',
  route: 'contact-us',
  document_type: 'CRM Lead',
  published: 0,
  fields: [{ fieldname: 'first_name', fieldtype: 'Data', label: 'First name' }],
  hidden_fields: [],
}

function serve(overrides = {}) {
  api.call.mockImplementation(async (method) => {
    if (method === 'get_form_config') return { ...SERVER_FORM, ...overrides }
    if (method === 'get_form_fields') return []
    if (method === 'save_form') return { route: 'contact-us', fields: [] }
    return null
  })
}

async function loadDraft(overrides) {
  serve(overrides)
  const onSaved = vi.fn()
  const draft = useFormDraft({ name: 'contact-us', onSaved })
  await flushPromises()
  api.call.mockClear()
  return { draft, onSaved }
}

const flushPromises = () => new Promise((resolve) => setTimeout(resolve))
const refuse = () =>
  api.call.mockImplementation(async () => {
    throw Object.assign(new Error('No'), { messages: ['No'] })
  })
const calls = (method) => api.call.mock.calls.filter(([m]) => m === method)

describe('useFormDraft', () => {
  beforeEach(() => {
    api.call.mockReset()
  })

  it('loads clean', async () => {
    const { draft } = await loadDraft()
    expect(draft.loaded.value).toBe(true)
    expect(draft.dirty.value).toBe(false)
  })

  it('marks an edit dirty, and a save clears it', async () => {
    const { draft, onSaved } = await loadDraft()
    draft.markDirty()
    expect(draft.dirty.value).toBe(true)
    await draft.saveNow()
    expect(calls('save_form')).toHaveLength(1)
    expect(draft.dirty.value).toBe(false)
    expect(onSaved).toHaveBeenCalledOnce()
  })

  it('does not save a clean draft', async () => {
    const { draft } = await loadDraft()
    await draft.saveNow()
    expect(calls('save_form')).toHaveLength(0)
  })

  it('stays dirty when an edit lands during the save', async () => {
    const { draft } = await loadDraft()
    draft.markDirty()
    let finish
    api.call.mockImplementation(
      () => new Promise((resolve) => (finish = resolve))
    )
    const saving = draft.saveNow()
    draft.markDirty()
    finish({ route: 'contact-us', fields: [] })
    await saving
    expect(draft.dirty.value).toBe(true)
  })

  it('stays dirty when the save fails', async () => {
    const { draft } = await loadDraft()
    draft.markDirty()
    refuse()
    await draft.saveNow()
    expect(draft.dirty.value).toBe(true)
  })

  it('publish saves pending edits with the published flag', async () => {
    const { draft } = await loadDraft()
    draft.markDirty()
    await draft.publish()
    const [, args] = calls('save_form')[0]
    expect(args.form.published).toBe(1)
    expect(draft.form.published).toBe(1)
    expect(draft.dirty.value).toBe(false)
  })

  it('publish refuses a hidden field with no default and stays a draft', async () => {
    const { draft } = await loadDraft({
      hidden_fields: [
        { fieldname: 'status', label: 'Status', fieldtype: 'Data' },
      ],
    })
    await draft.publish()
    expect(calls('save_form')).toHaveLength(0)
    expect(draft.form.published).toBe(0)
  })

  it('publish returns to draft when the server refuses', async () => {
    const { draft } = await loadDraft()
    refuse()
    await draft.publish()
    expect(draft.form.published).toBe(0)
  })

  it('unpublish acts at once and leaves edits unsaved', async () => {
    const { draft } = await loadDraft({ published: 1 })
    draft.markDirty()
    await draft.unpublish()
    expect(calls('set_published')[0][1]).toEqual({
      name: 'contact-us',
      published: 0,
    })
    expect(calls('save_form')).toHaveLength(0)
    expect(draft.form.published).toBe(0)
    expect(draft.dirty.value).toBe(true)
  })

  it('unpublish keeps the form published when the server refuses', async () => {
    const { draft } = await loadDraft({ published: 1 })
    refuse()
    await draft.unpublish()
    expect(draft.form.published).toBe(1)
  })
})
