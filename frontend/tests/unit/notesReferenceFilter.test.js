import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { createApp, h, nextTick, reactive } from 'vue'

const state = vi.hoisted(() => ({
  route: { query: {} },
  replace: vi.fn(),
  openNote: vi.fn(),
}))
vi.mock('vue-router', () => ({
  useRoute: () => reactive(state.route),
  useRouter: () => ({ replace: state.replace }),
}))
vi.mock('@/components/LayoutHeader.vue', () => ({
  default: {
    setup:
      (_, { slots }) =>
      () =>
        h('header', [slots['left-header']?.(), slots['right-header']?.()]),
  },
}))
vi.mock('@/components/ViewBreadcrumbs.vue', () => ({
  default: { render: () => null },
}))
vi.mock('@/components/UserAvatar.vue', () => ({
  default: { render: () => null },
}))
vi.mock('@/components/Icons/NoteIcon.vue', () => ({
  default: { render: () => null },
}))
vi.mock('@/components/ListViews/EmptyState.vue', () => ({
  default: { render: () => null },
}))
vi.mock('@/components/ViewControls.vue', () => ({
  default: {
    props: ['filters', 'filtersLabel'],
    emits: ['clearFilters'],
    setup:
      (props, { emit }) =>
      () =>
        h('div', [
          h(
            'output',
            { 'data-filters': true },
            JSON.stringify(props.filters || {}),
          ),
          props.filtersLabel
            ? h(
                'button',
                { onClick: () => emit('clearFilters') },
                props.filtersLabel,
              )
            : null,
        ]),
  },
}))
vi.mock('@/components/Controls/Link.vue', () => ({
  default: {
    props: ['doctype', 'value', 'label'],
    emits: ['change'],
    setup:
      (props, { emit }) =>
      () =>
        h('input', {
          'data-doctype': props.doctype,
          'aria-label': props.label,
          value: props.value,
          onInput: (event) => emit('change', event.target.value),
        }),
  },
}))
vi.mock('@/composables/doctypeModal', () => ({
  useDoctypeModal: () => ({ showModal: vi.fn() }),
}))
vi.mock('@/composables/noteView', () => ({
  useNoteView: () => ({
    openNote: state.openNote,
    noteLink: vi.fn(),
    loadLinkedTitles: vi.fn(),
    linkedRoute: () => null,
    linkedLabel: vi.fn(),
  }),
}))
vi.mock('@/stores/users', () => ({
  usersStore: () => ({ getUser: () => ({ full_name: 'Test User' }) }),
}))
vi.mock('@/utils', () => ({
  timeAgo: vi.fn(),
  formatDate: vi.fn(),
  sanitizeHTML: vi.fn(),
  copyToClipboard: vi.fn(),
}))
vi.mock('@framework/ui/telemetry', () => ({
  useTelemetry: () => ({ capture: vi.fn() }),
}))
vi.mock('frappe-ui', () => ({
  call: vi.fn(),
  Dropdown: { render: () => null },
  Tooltip: { render: () => null },
  FormControl: {
    props: ['modelValue', 'options', 'label'],
    emits: ['update:modelValue'],
    setup:
      (props, { emit }) =>
      () =>
        h(
          'select',
          {
            'aria-label': props.label,
            value: props.modelValue,
            onChange: (event) => emit('update:modelValue', event.target.value),
          },
          props.options.map((option) =>
            h('option', { value: option.value }, option.label),
          ),
        ),
  },
}))
vi.mock('frappe-ui/experimental', () => ({
  ListFooter: { render: () => null },
}))

import Notes from '@/pages/Notes.vue'
import { useRoute } from 'vue-router'

let app, root
const route = useRoute()
beforeEach(() => {
  route.query = {}
  state.openNote.mockClear()
  state.replace.mockReset().mockImplementation(({ query }) => {
    route.query = query
    return Promise.resolve()
  })
})
afterEach(() => {
  app?.unmount()
  root?.remove()
})
function mountNotes(query = {}) {
  route.query = query
  root = document.createElement('div')
  document.body.append(root)
  app = createApp(Notes)
  app.config.globalProperties.__ = (text) => text
  // Match the application's globally registered Button component.
  // eslint-disable-next-line vue/no-reserved-component-names
  app.component('Button', { render: () => null })
  app.mount(root)
}
const filters = () =>
  JSON.parse(root.querySelector('[data-filters]').textContent)
async function chooseType(doctype) {
  const control = root.querySelector('select')
  control.value = doctype
  control.dispatchEvent(new Event('change'))
  await nextTick()
}
async function chooseRecord(name) {
  const control = root.querySelector('input')
  control.value = name
  control.dispatchEvent(new Event('input'))
  await nextTick()
}

describe('Notes reference filters', () => {
  it('filters the server-side list by type and record, clearing the record when its type changes', async () => {
    mountNotes({ view: 'saved-view' })
    expect(filters()).toEqual({})
    await chooseType('CRM Lead')
    expect(filters()).toEqual({ reference_doctype: 'CRM Lead' })
    expect(root.querySelector('input').dataset.doctype).toBe('CRM Lead')
    await chooseRecord('CRM-LEAD-0001')
    expect(filters()).toEqual({
      reference_doctype: 'CRM Lead',
      reference_docname: 'CRM-LEAD-0001',
    })
    await chooseType('CRM Deal')
    expect(filters()).toEqual({ reference_doctype: 'CRM Deal' })
    expect(root.querySelector('input').dataset.doctype).toBe('CRM Deal')
    expect(root.querySelector('input').value).toBe('')
    expect(route.query.view).toBe('saved-view')
  })

  it('restores a specific deal filter from the URL and clears only its own query keys', async () => {
    mountNotes({
      view: 'saved-view',
      reference_doctype: 'CRM Deal',
      reference_docname: 'DEAL-0001',
    })
    expect(root.querySelector('select').value).toBe('CRM Deal')
    expect(root.querySelector('input').value).toBe('DEAL-0001')
    expect(filters()).toEqual({
      reference_doctype: 'CRM Deal',
      reference_docname: 'DEAL-0001',
    })
    root.querySelector('button').click()
    await nextTick()
    expect(filters()).toEqual({})
    expect(root.querySelector('input')).toBeNull()
    expect(route.query).toEqual({ view: 'saved-view' })
  })

  it('opens a shared note without removing the saved view or reference scope', async () => {
    mountNotes({
      open: 'NOTE-0001',
      view: 'saved-view',
      reference_doctype: 'CRM Lead',
      reference_docname: 'LEAD-0001',
    })
    await nextTick()
    expect(state.openNote).toHaveBeenCalledWith(
      { name: 'NOTE-0001' },
      expect.any(Object),
    )
    expect(route.query).toEqual({
      view: 'saved-view',
      reference_doctype: 'CRM Lead',
      reference_docname: 'LEAD-0001',
    })
    expect(filters()).toEqual({
      reference_doctype: 'CRM Lead',
      reference_docname: 'LEAD-0001',
    })
  })

  it('ignores an incomplete or unsupported reference scope', () => {
    mountNotes({ reference_docname: 'SAME-NAME', reference_doctype: 'User' })
    expect(filters()).toEqual({})
    expect(root.querySelector('input')).toBeNull()
  })
})
