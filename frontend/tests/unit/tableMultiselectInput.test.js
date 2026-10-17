/* eslint-disable vue/one-component-per-file -- This test mounts a fixture with small component stubs. */
import { createApp, h, nextTick, reactive } from 'vue'
import { describe, expect, it, vi } from 'vitest'
import Control from '@/components/Controls/TableMultiselectInput.vue'

vi.mock('@/stores/meta', () => ({
  getMeta: () => ({
    getFields: () => [
      { fieldtype: 'Link', fieldname: 'item', options: 'Item' },
    ],
  }),
}))
vi.mock('@/composables/document', () => ({ createDocument: vi.fn() }))
vi.mock('@/components/Controls/Link.vue', async () => {
  const { h } = await import('vue')
  return {
    default: {
      props: ['filters'],
      setup:
        (props, { slots }) =>
        () =>
          h(
            'div',
            {
              'data-filters': JSON.stringify(props.filters),
            },
            slots.target?.({ togglePopover: () => {} }),
          ),
    },
  }
})

describe('TableMultiselectInput', () => {
  it('forwards filters and reacts to field constraints and selected values', async () => {
    const state = reactive({
      filters: { name: ['like', 'Item-%'] },
      values: [],
    })
    const container = document.createElement('div')
    document.body.append(container)
    const app = createApp({
      render: () =>
        h(Control, {
          doctype: 'Test Child',
          filters: state.filters,
          modelValue: state.values,
        }),
    })
    app.config.globalProperties.__ = (value) => value
    // eslint-disable-next-line vue/no-reserved-component-names -- Match Frappe UI's existing global component name.
    app.component('Button', { render: () => h('button') })
    app.component('ErrorMessage', { render: () => null })
    try {
      app.mount(container)
      await nextTick()
      const filters = () =>
        JSON.parse(container.querySelector('[data-filters]').dataset.filters)
      expect(filters()).toEqual([
        ['name', 'like', 'Item-%'],
        ['name', 'not in', []],
      ])
      state.values = [{ item: 'Item-1' }]
      state.filters = { enabled: 1 }
      await nextTick()
      expect(filters()).toEqual([
        ['enabled', '=', 1],
        ['name', 'not in', ['Item-1']],
      ])
    } finally {
      app.unmount()
      container.remove()
    }
  })
})
