import { describe, it, expect, vi } from 'vitest'
import { createApp, defineComponent, h, nextTick } from 'vue'
import Grid from '@/components/Controls/Grid.vue'

const linkFilters = vi.hoisted(() => [])

vi.mock('@/components/Controls/Link.vue', async () => {
  const { defineComponent } = await import('vue')
  return {
    default: defineComponent({
      props: { filters: { type: Object, default: null } },
      setup(props) {
        linkFilters.push(props.filters)
        return () => null
      },
    }),
  }
})

vi.mock('@/components/Controls/GeolocationControl.vue', () => ({
  default: { render: () => null },
}))
vi.mock('@/components/Controls/GridFieldsEditorModal.vue', () => ({
  default: { render: () => null },
}))
vi.mock('@/components/Controls/GridRowFieldsModal.vue', () => ({
  default: { render: () => null },
}))
vi.mock('@/components/Controls/GridRowModal.vue', () => ({
  default: { render: () => null },
}))
vi.mock('@/composables/document', () => ({ createDocument: vi.fn() }))

vi.mock('vuedraggable', async () => {
  const { defineComponent, h } = await import('vue')
  return {
    default: defineComponent({
      props: { modelValue: { type: Array, default: () => [] } },
      setup(props, { slots }) {
        return () =>
          h(
            'div',
            props.modelValue.map((element, index) =>
              slots.item({ element, index }),
            ),
          )
      },
    }),
  }
})

vi.mock('@/stores/users', () => ({
  usersStore: () => ({
    users: { data: { crmUsers: [{ name: 'agent@example.com' }] } },
    getUser: () => ({ full_name: '' }),
  }),
}))

vi.mock('@/stores/meta', () => ({
  getMeta: () => ({
    getGridViewSettings: () => [],
    getGridSettings: () => ({ editable_grid: 1 }),
    getFields: () => gridFields,
    getFloatWithPrecision: () => 0,
    getCurrencyWithPrecision: () => 0,
    getFormattedCurrency: () => '',
  }),
}))

const gridFields = [
  {
    fieldname: 'contact',
    label: 'Contact',
    fieldtype: 'Link',
    options: 'Contact',
    in_list_view: 1,
    link_filters: '[["Contact","company","=","eval:doc.company"]]',
  },
  {
    fieldname: 'assignee',
    label: 'Assignee',
    fieldtype: 'Link',
    options: 'User',
    in_list_view: 1,
    link_filters: '[["User","department","=","eval:doc.department"]]',
  },
]

async function renderGrid(rows) {
  linkFilters.length = 0
  const app = createApp(
    defineComponent({
      setup: () => () =>
        h(Grid, {
          modelValue: rows,
          parent: { company: 'Parent Co' },
          doctype: 'Deal Line',
          parentDoctype: 'CRM Deal',
          parentFieldname: 'lines',
        }),
    }),
  )
  app.config.globalProperties.__ = (text) => text
  app.mount(document.createElement('div'))
  await nextTick()
  return app
}

describe('Grid link filters', () => {
  it('evaluates eval:doc filters against each row', async () => {
    const app = await renderGrid([
      { name: 'row-1', company: 'ACME', department: 'Sales' },
      { name: 'row-2', company: 'Globex', department: 'Support' },
    ])

    const crmUsers = ['in', ['agent@example.com']]
    expect(linkFilters).toEqual([
      { company: ['=', 'ACME'] },
      { name: crmUsers, ignore_user_type: 1, department: ['=', 'Sales'] },
      { company: ['=', 'Globex'] },
      { name: crmUsers, ignore_user_type: 1, department: ['=', 'Support'] },
    ])

    app.unmount()
  })
})
