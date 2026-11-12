import { beforeEach, describe, expect, it, vi } from 'vitest'
import { reactive, ref } from 'vue'

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
import { useEditorDrag } from '../../../crm/fcrm/frontend/forms/builder/useEditorDrag.js'
import { useEditorSelection } from '../../../crm/fcrm/frontend/forms/builder/useEditorSelection.js'

const CATALOG = [
  { fieldname: 'first_name', fieldtype: 'Data', label: 'First Name', reqd: 1 },
  { fieldname: 'mobile_no', fieldtype: 'Data', label: 'Mobile No' },
  { fieldname: 'email', fieldtype: 'Data', label: 'Email' },
  {
    fieldname: 'source',
    fieldtype: 'Link',
    label: 'Source',
    options: 'CRM Lead Source',
  },
  {
    fieldname: 'annual_revenue',
    fieldtype: 'Currency',
    label: 'Annual Revenue',
  },
]

const SERVER_FORM = {
  title: 'Contact us',
  route: 'contact-us',
  document_type: 'CRM Lead',
  published: 0,
  fields: [
    {
      fieldname: 'first_name',
      fieldtype: 'Data',
      label: 'First Name',
      reqd: 1,
    },
    { fieldname: 'email', fieldtype: 'Data', label: 'Email' },
  ],
  hidden_fields: [],
}

function serve(overrides = {}) {
  api.call.mockImplementation(async (method) => {
    if (method === 'get_form_config') return { ...SERVER_FORM, ...overrides }
    if (method === 'get_form_fields') return CATALOG
    if (method === 'save_form') return { route: 'contact-us', fields: [] }
    return null
  })
}

async function loadDraft(overrides) {
  serve(overrides)
  const draft = useFormDraft({ name: 'contact-us' })
  await flushPromises()
  api.call.mockClear()
  return draft
}

const flushPromises = () => new Promise((resolve) => setTimeout(resolve))
const calls = (method) => api.call.mock.calls.filter(([m]) => m === method)
const names = (items) => items.map((f) => f.fieldname)
const hiddenEntry = (fieldname, value = '') => ({
  ...CATALOG.find((f) => f.fieldname === fieldname),
  options: '',
  default: value,
})

describe('the hidden block', () => {
  beforeEach(() => api.call.mockReset())

  it('lists a missing row for a required field that is neither on the form nor hidden', async () => {
    const draft = await loadDraft({ fields: [SERVER_FORM.fields[1]] })
    const missing = draft.hiddenRows.value.filter((h) => h.missing)
    expect(names(missing)).toEqual(['first_name'])
    expect(draft.isMissingRow(missing[0])).toBe(true)
  })

  it('has no missing row once the required field is hidden with a value', async () => {
    const draft = await loadDraft({
      fields: [SERVER_FORM.fields[1]],
      hidden_fields: [hiddenEntry('first_name', 'Guest')],
    })
    expect(draft.hiddenRows.value.filter((h) => h.missing)).toHaveLength(0)
    expect(draft.isMissingRow(draft.hiddenRows.value[0])).toBe(false)
  })

  it('shows an empty required hidden row as missing, until the user is entering a value', async () => {
    const draft = await loadDraft({
      fields: [SERVER_FORM.fields[1]],
      hidden_fields: [hiddenEntry('first_name')],
    })
    const row = draft.hiddenRows.value[0]
    expect(draft.isMissingRow(row)).toBe(true)
    draft.setHiddenValue(row)
    expect(draft.isMissingRow(row)).toBe(false)
  })

  it('adds a Check row unticked, so it has a value and publishes', async () => {
    const draft = await loadDraft()
    const af = {
      fieldname: 'unsubscribed',
      fieldtype: 'Check',
      label: 'Unsubscribed',
    }
    draft.addHiddenField({ value: af.fieldname, af })
    const row = draft.hiddenRows.value.find(
      (h) => h.fieldname === 'unsubscribed',
    )
    expect(row.default).toBe('0')
    expect(draft.isMissingRow(row)).toBe(false)
  })

  it('saves each typed control value in the format the server accepts', async () => {
    const draft = await loadDraft({
      hidden_fields: [
        {
          fieldname: 'unsubscribed',
          fieldtype: 'Check',
          label: 'Unsubscribed',
          default: '0',
        },
        {
          fieldname: 'no_of_employees',
          fieldtype: 'Int',
          label: 'Employees',
          default: '',
        },
        hiddenEntry('annual_revenue'),
      ],
    })
    const [check, int, currency] = draft.hiddenRows.value
    draft.setHiddenDefault(check, true)
    draft.setHiddenDefault(int, '12.7')
    draft.setHiddenDefault(currency, '2500.5')
    await draft.saveNow()
    const saved = calls('save_form')[0][1].form.hidden_fields
    expect(saved.map((h) => h.default)).toEqual(['1', '12', '2500.5'])
  })

  it('keeps the value control for an empty hidden row the record does not require', async () => {
    const draft = await loadDraft({ hidden_fields: [hiddenEntry('source')] })
    expect(draft.isMissingRow(draft.hiddenRows.value[0])).toBe(false)
  })

  it('has no missing row for a required field that has a default', async () => {
    const catalog = CATALOG.map((f) =>
      f.fieldname === 'first_name' ? { ...f, default: 'Guest' } : f,
    )
    api.call.mockImplementation(async (method) =>
      method === 'get_form_fields'
        ? catalog
        : method === 'get_form_config'
          ? { ...SERVER_FORM, fields: [SERVER_FORM.fields[1]] }
          : null,
    )
    const draft = useFormDraft({ name: 'contact-us' })
    await flushPromises()
    expect(draft.hiddenRows.value.filter((h) => h.missing)).toHaveLength(0)
  })

  it('"Add to form" puts the field at the end of the last section and drops it from hidden', async () => {
    const draft = await loadDraft({
      hidden_fields: [hiddenEntry('source', 'Web')],
    })
    const field = draft.addHiddenToForm(draft.hiddenRows.value[0])
    const lastColumn = draft.sections.value.at(-1).columns.at(-1)
    expect(lastColumn.items.at(-1).fieldname).toBe('source')
    expect(field.options).toBe('CRM Lead Source')
    expect(draft.hiddenFields.value).toHaveLength(0)
    expect(names(draft.form.fields)).toContain('source')
    expect(draft.dirty.value).toBe(true)
  })

  it('a field dropped into the block lands at the drop index', async () => {
    const draft = await loadDraft({
      hidden_fields: [
        hiddenEntry('source', 'Web'),
        hiddenEntry('annual_revenue', '1'),
      ],
    })
    draft.onHiddenChange({
      added: { element: { fieldname: 'mobile_no' }, newIndex: 1 },
    })
    expect(names(draft.hiddenFields.value)).toEqual([
      'source',
      'mobile_no',
      'annual_revenue',
    ])
    draft.onHiddenChange({
      added: { element: { fieldname: 'email' }, newIndex: 99 },
    })
    expect(names(draft.hiddenFields.value).at(-1)).toBe('email')
  })
})

describe('editing the form', () => {
  beforeEach(() => api.call.mockReset())

  it('offers the unused fields sorted by label, each with an icon', async () => {
    const draft = await loadDraft()
    const options = draft.availableFieldOptions.value
    expect(options.map((o) => o.label)).toEqual([
      'Annual Revenue',
      'Mobile No',
      'Source',
    ])
    expect(options.every((o) => o.icon)).toBe(true)
  })

  it('setColumns adds empty columns and folds removed ones into the previous', async () => {
    const draft = await loadDraft()
    const sec = draft.sections.value[0]
    draft.setColumns(sec, 2)
    expect(sec.columns).toHaveLength(2)
    expect(sec.columns[1].items).toHaveLength(0)
    draft.addFieldToColumn(sec.columns[1], CATALOG[1])
    draft.setColumns(sec, 1)
    expect(sec.columns).toHaveLength(1)
    expect(names(sec.columns[0].items)).toEqual([
      'first_name',
      'email',
      'mobile_no',
    ])
  })

  it('a section "Add field" lands after the selected field', async () => {
    const draft = await loadDraft()
    const sec = draft.sections.value[0]
    const [first] = sec.columns[0].items
    draft.addFieldToSection(sec, draft.availableFieldOptions.value[0], first)
    expect(names(sec.columns[0].items)).toEqual([
      'first_name',
      'annual_revenue',
      'email',
    ])
  })

  it('a section "Add field" with no selection lands in the shortest column', async () => {
    const draft = await loadDraft()
    const sec = draft.sections.value[0]
    draft.setColumns(sec, 2)
    draft.addFieldToSection(sec, CATALOG[1])
    expect(names(sec.columns[1].items)).toEqual(['mobile_no'])
  })

  it('publish is refused while a required field is missing, and stays a draft', async () => {
    const draft = await loadDraft({ fields: [SERVER_FORM.fields[1]] })
    draft.markDirty()
    await draft.publish()
    expect(calls('save_form')).toHaveLength(0)
    expect(draft.form.published).toBe(0)
    expect(api.toast.error).toHaveBeenCalledWith(
      expect.stringContaining('First Name'),
    )
  })

  it('publish is refused while a hidden row has no value, and the required row turns red again', async () => {
    const draft = await loadDraft({
      fields: [SERVER_FORM.fields[1]],
      hidden_fields: [hiddenEntry('first_name'), hiddenEntry('source')],
    })
    const [first, source] = draft.hiddenRows.value
    draft.setHiddenValue(first)
    await draft.publish()
    expect(calls('save_form')).toHaveLength(0)
    expect(api.toast.error).toHaveBeenCalledWith(
      expect.stringContaining('First Name, Source'),
    )
    expect(draft.isMissingRow(first)).toBe(true)
    expect(draft.isMissingRow(source)).toBe(false)
  })
})

describe('useEditorSelection', () => {
  let draft, drag, sel
  const key = (k, target = document.body) => ({
    key: k,
    target,
    preventDefault: vi.fn(),
  })

  beforeEach(async () => {
    api.call.mockReset()
    vi.spyOn(console, 'warn').mockImplementation(() => {}) // onBeforeUnmount outside a component
    draft = reactive(await loadDraft())
    drag = { active: vi.fn(() => false), cancel: vi.fn() }
    sel = useEditorSelection({ draft, drag })
    sel.selectField(draft.form.fields.find((f) => f.fieldname === 'email'))
  })

  it('Delete removes the selected field', () => {
    sel.onKeydown(key('Delete'))
    expect(names(draft.form.fields)).not.toContain('email')
    expect(sel.field.value).toBe(null)
  })

  it('Delete is ignored while typing', () => {
    sel.onKeydown(key('Backspace', document.createElement('input')))
    expect(names(draft.form.fields)).toContain('email')
    expect(sel.field.value).not.toBe(null)
  })

  it('Escape clears the selection, or cancels a drag first', () => {
    drag.active.mockReturnValue(true)
    sel.onKeydown(key('Escape'))
    expect(drag.cancel).toHaveBeenCalledOnce()
    expect(sel.field.value).not.toBe(null)
    drag.active.mockReturnValue(false)
    sel.onKeydown(key('Escape'))
    expect(sel.field.value).toBe(null)
  })

  it('removeSelected removes the field and clears', () => {
    sel.removeSelected()
    expect(names(draft.form.fields)).not.toContain('email')
    expect(sel.field.value).toBe(null)
  })
})

describe('useEditorDrag', () => {
  let draft, layer, drag

  beforeEach(async () => {
    api.call.mockReset()
    draft = reactive(
      await loadDraft({ hidden_fields: [hiddenEntry('source', 'Web')] }),
    )
    layer = ref({
      start: vi.fn(),
      end: vi.fn(() => false),
      pos: { x: 10, y: 20 },
    })
    drag = useEditorDrag({ draft, layer })
  })

  const column = () => draft.sections[0].columns[0]
  const startOn = (element) =>
    drag.startField({ item: { __draggable_context: { element } } })

  it('Escape puts every list back as it was', () => {
    const email = column().items[1]
    startOn(email)
    expect(layer.value.start).toHaveBeenCalledWith(
      expect.objectContaining({ label: 'Email' }),
      true,
    )
    column().items.splice(1, 1)
    draft.hiddenFields.push(hiddenEntry('email'))
    drag.cancel({ preventDefault: vi.fn() })
    expect(drag.end()).toEqual({ cancelled: true, removed: null })
    expect(names(column().items)).toEqual(['first_name', 'email'])
    expect(names(draft.hiddenFields)).toEqual(['source'])
    expect(drag.active()).toBe(false)
  })

  it('Escape leaves a clean draft clean', () => {
    expect(draft.dirty).toBe(false)
    startOn(column().items[1])
    draft.hiddenFields.push(hiddenEntry('email'))
    draft.markDirty()
    drag.cancel({ preventDefault: vi.fn() })
    drag.end()
    expect(draft.dirty).toBe(false)
  })

  it('a release over the bin reports the field and never leaves it hidden', () => {
    const email = column().items[1]
    startOn(email)
    draft.hiddenFields.push(hiddenEntry('email'))
    layer.value.end.mockReturnValue(true)
    expect(drag.end()).toEqual({ cancelled: false, removed: email })
    expect(names(draft.hiddenFields)).toEqual(['source'])
  })

  it('a normal drop keeps the move', () => {
    startOn(column().items[1])
    column().items.reverse()
    expect(drag.end()).toEqual({ cancelled: false, removed: null })
    expect(names(column().items)).toEqual(['email', 'first_name'])
  })
})
