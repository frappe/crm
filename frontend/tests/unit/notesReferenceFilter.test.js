/* eslint-disable vue/one-component-per-file -- Test harnesses and component stubs share this file. */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { createApp, h, nextTick } from 'vue'
import { createRouter, createMemoryHistory, RouterView } from 'vue-router'

const state = vi.hoisted(() => ({
  controlsMounted: vi.fn(),
  openNote: vi.fn(),
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
    setup(props, { emit }) {
      state.controlsMounted()
      return () =>
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
        ])
    },
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
vi.mock('@/stores/session', () => ({
  sessionStore: () => ({ isLoggedIn: true }),
}))
vi.mock('@/stores/views', () => ({ viewsStore: () => ({}) }))
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
    props: ['modelValue', 'options', 'label', 'type'],
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

let app, root, router
beforeEach(() => {
  state.openNote.mockClear()
  state.controlsMounted.mockClear()
})
afterEach(() => {
  app?.unmount()
  root?.remove()
})
async function mountNotes(query = {}) {
  // Use the production route's metadata and App's keyed router-view behavior.
  const { default: appRouter } = await import('@/router')
  const route = appRouter.getRoutes().find((route) => route.name === 'Notes')
  router = createRouter({
    history: createMemoryHistory(),
    routes: [
      {
        path: route.path,
        name: route.name,
        meta: route.meta,
        component: Notes,
      },
    ],
  })
  await router.push({ name: 'Notes', params: { viewType: 'list' }, query })
  root = document.createElement('div')
  document.body.append(root)
  app = createApp({
    render: () =>
      h(RouterView, {
        key:
          router.currentRoute.value.meta.viewKey ||
          router.currentRoute.value.fullPath.split('#')[0],
      }),
  })
  app.use(router)
  app.config.globalProperties.__ = (text) => text
  // Match the application's globally registered Button component.
  // eslint-disable-next-line vue/no-reserved-component-names
  app.component('Button', { render: () => null })
  app.mount(root)
  await settle()
}
async function settle() {
  // Wait for both router navigation and Vue's queued render.
  await new Promise((resolve) => setTimeout(resolve, 0))
  await nextTick()
}
const filters = () =>
  JSON.parse(root.querySelector('[data-filters]').textContent)
async function chooseType(doctype) {
  const control = root.querySelector('select')
  control.value = doctype
  control.dispatchEvent(new Event('change'))
  await settle()
}
async function chooseRecord(name) {
  const control = root.querySelector('input')
  control.value = name
  control.dispatchEvent(new Event('input'))
  await settle()
}

describe('Notes reference filters', () => {
  it('filters the server-side list by type and record, clearing the record when its type changes', async () => {
    await mountNotes({ view: 'saved-view' })
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
    expect(router.currentRoute.value.query.view).toBe('saved-view')
  })

  it('restores a specific deal filter from the URL and clears only its own query keys', async () => {
    await mountNotes({
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
    await settle()
    expect(filters()).toEqual({})
    expect(root.querySelector('input')).toBeNull()
    expect(router.currentRoute.value.query).toEqual({ view: 'saved-view' })
  })

  it('opens a shared note without removing the saved view or reference scope', async () => {
    await mountNotes({
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
    await router.push({
      query: { ...router.currentRoute.value.query, open: 'NOTE-0002' },
    })
    await settle()
    expect(state.openNote).toHaveBeenLastCalledWith(
      { name: 'NOTE-0002' },
      expect.any(Object),
    )
    expect(router.currentRoute.value.query).toEqual({
      view: 'saved-view',
      reference_doctype: 'CRM Lead',
      reference_docname: 'LEAD-0001',
    })
    expect(filters()).toEqual({
      reference_doctype: 'CRM Lead',
      reference_docname: 'LEAD-0001',
    })
  })

  it('ignores an incomplete or unsupported reference scope', async () => {
    await mountNotes({
      reference_docname: 'SAME-NAME',
      reference_doctype: 'User',
    })
    expect(filters()).toEqual({})
    expect(root.querySelector('input')).toBeNull()
  })

  it('keeps the current controls while changing scope on a saved view', async () => {
    await mountNotes({ view: 'saved-view' })
    await chooseType('CRM Lead')
    await chooseRecord('LEAD-0001')
    await chooseType('CRM Deal')
    expect(state.controlsMounted).toHaveBeenCalledTimes(1)
    expect(router.currentRoute.value.query.view).toBe('saved-view')
  })

  it('retains the record scope when selecting a saved view and returning to the standard view', async () => {
    const scope = {
      reference_doctype: 'CRM Lead',
      reference_docname: 'LEAD-0001',
    }
    await mountNotes(scope)
    await router.push({
      name: 'Notes',
      params: { viewType: 'list' },
      query: { view: 'saved-view' },
    })
    expect(router.currentRoute.value.query).toEqual({
      ...scope,
      view: 'saved-view',
    })
    expect(filters()).toEqual(scope)
    await router.push({ name: 'Notes', params: { viewType: 'list' } })
    expect(router.currentRoute.value.query).toEqual(scope)
    expect(filters()).toEqual(scope)
    // Explicitly clearing the scope must still work.
    await chooseType('')
    expect(filters()).toEqual({})
  })
})
