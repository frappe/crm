/* eslint-disable vue/one-component-per-file -- Test harnesses and component stubs share this file. */
import { afterEach, describe, expect, it, vi } from 'vitest'
import { createApp, h, nextTick, reactive, ref } from 'vue'

const state = vi.hoisted(() => ({ requests: [] }))
vi.mock('vue-router', () => ({
  useRoute: () => ({
    name: 'Notes',
    query: { view: 'saved' },
    params: { viewType: 'list' },
  }),
  useRouter: () => ({ push: vi.fn() }),
}))
vi.mock('@/stores/settings', () => ({ getSettings: () => ({ brand: {} }) }))
vi.mock('@/stores/global', () => ({ globalStore: () => ({}) }))
vi.mock('@/stores/views', () => ({
  viewsStore: () => ({
    getView: () => ({
      name: 'saved',
      filters: '{"owner":"saved-owner"}',
      order_by: 'modified desc',
    }),
    getDefaultView: () => null,
    reload: vi.fn(),
  }),
}))
vi.mock('@/stores/users', () => ({
  usersStore: () => ({
    isManager: () => false,
    getUser: () => ({ name: 'me' }),
  }),
}))
vi.mock('@/stores/organizations', () => ({ organizationsStore: () => ({}) }))
vi.mock('@/stores/statuses', () => ({ statusesStore: () => ({}) }))
vi.mock('@/stores/meta', () => ({ getMeta: () => ({ getFields: () => [] }) }))
vi.mock('@/utils', () => ({ isEmoji: () => false }))
vi.mock('@/composables/settings', () => ({ isMobileView: false }))
vi.mock('@/composables/useCommandPalette', () => ({
  commandPaletteOpen: ref(false),
  useCommandPaletteContext: vi.fn(),
}))
vi.mock('@framework/ui/components/GroupBy', () => ({
  GroupBy: { render: () => null },
  parseGroupBy: () => null,
  serializeGroupBy: () => null,
}))
vi.mock('@/components/Icon.vue', () => ({ default: { render: () => null } }))
vi.mock('@/components/QuickFilterField.vue', () => ({
  default: { render: () => null },
}))
vi.mock('@/components/Modals/ViewModal.vue', () => ({
  default: { render: () => null },
}))
vi.mock('@/components/GroupBy.vue', () => ({ default: { render: () => null } }))
vi.mock('@/components/FadedScrollableDiv.vue', () => ({
  default: { render: () => null },
}))
vi.mock('@/components/ColumnSettings.vue', () => ({
  default: { render: () => null },
}))
vi.mock('@/components/Kanban/KanbanSettings.vue', () => ({
  default: { render: () => null },
}))
vi.mock('@/components/Modals/LostReasonModal.vue', () => ({
  default: { render: () => null },
}))
vi.mock('@/components/Filter.vue', () => ({
  default: {
    emits: ['update'],
    setup:
      (_, { emit }) =>
      () =>
        h(
          'button',
          {
            'data-filter': '',
            onClick: () => emit('update', { owner: 'unsaved-owner' }),
          },
          'Filter',
        ),
  },
}))
vi.mock('@/components/SortBy.vue', () => ({
  default: {
    emits: ['update'],
    setup:
      (_, { emit }) =>
      () =>
        h(
          'button',
          { 'data-sort': '', onClick: () => emit('update', 'creation asc') },
          'Sort',
        ),
  },
}))
vi.mock('frappe-ui', () => ({
  Combobox: { render: () => null },
  Dropdown: { render: () => null },
  Tooltip: { render: () => null },
  toast: {},
  call: vi.fn(),
  usePageMeta: vi.fn(),
  createResource(options) {
    const resource = reactive({
      params: options.params,
      data:
        options.url === 'crm.api.doc.get_data' ? { data: [], views: [] } : [],
      loading: false,
    })
    resource.reload = resource.fetch = vi.fn(() => {
      if (options.url !== 'crm.api.doc.get_data') return Promise.resolve()
      resource.loading = true
      const params = JSON.parse(JSON.stringify(resource.params))
      return new Promise((resolve) => {
        state.requests.push({
          params,
          resource,
          finish: () => {
            options.onSuccess?.(resource.data)
            resource.loading = false
            resolve(resource.data)
          },
        })
      })
    })
    if (options.auto) resource.reload()
    return resource
  },
}))

import ViewControls from '@/components/ViewControls.vue'

let app, root
const scope = ref({})
async function mountControls() {
  state.requests = []
  scope.value = {}
  root = document.createElement('div')
  document.body.append(root)
  const list = ref({})
  app = createApp({
    render: () =>
      h(ViewControls, {
        doctype: 'FCRM Note',
        filters: scope.value,
        options: { hideColumnsButton: true, cache: false },
        modelValue: list.value,
        'onUpdate:modelValue': (value) => {
          list.value = value
        },
      }),
  })
  app.config.globalProperties.__ = (text) => text
  // eslint-disable-next-line vue/no-reserved-component-names
  app.component('Button', {
    props: { label: { type: String, default: '' } },
    render() {
      return h('button', this.label)
    },
  })
  // eslint-disable-next-line vue/no-reserved-component-names
  app.component('Dialog', { render: () => null })
  app.mount(root)
  await nextTick()
}
async function finishLatest() {
  state.requests.at(-1).finish()
  await nextTick()
}
afterEach(() => {
  app?.unmount()
  root?.remove()
})

describe('ViewControls page filters', () => {
  it('keeps unsaved filters, sorting, and the Save Changes state when scope changes or clears', async () => {
    await mountControls()
    await finishLatest()
    root.querySelector('[data-filter]').click()
    await finishLatest()
    root.querySelector('[data-sort]').click()
    await finishLatest()
    scope.value = {
      reference_doctype: 'CRM Lead',
      reference_docname: 'LEAD-0001',
    }
    await nextTick()
    expect(state.requests.at(-1).params).toMatchObject({
      filters: { owner: 'unsaved-owner' },
      order_by: 'creation asc',
      default_filters: scope.value,
    })
    expect(root.textContent).toContain('Save Changes')
    await finishLatest()
    scope.value = {}
    await nextTick()
    expect(state.requests.at(-1).params).toMatchObject({
      filters: { owner: 'unsaved-owner' },
      order_by: 'creation asc',
      default_filters: {},
    })
    expect(root.textContent).toContain('Save Changes')
    await finishLatest()
  })

  it('waits for an in-flight request and then fetches the latest scope', async () => {
    await mountControls()
    scope.value = { reference_doctype: 'CRM Lead' }
    await nextTick()
    scope.value = {
      reference_doctype: 'CRM Deal',
      reference_docname: 'DEAL-0001',
    }
    await nextTick()
    expect(state.requests).toHaveLength(1)
    await finishLatest()
    expect(state.requests).toHaveLength(2)
    expect(state.requests.at(-1).params.default_filters).toEqual(scope.value)
    await finishLatest()
    expect(state.requests.at(-1).resource.params.default_filters).toEqual(
      scope.value,
    )
  })
})
