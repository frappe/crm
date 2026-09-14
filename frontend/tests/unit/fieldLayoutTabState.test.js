import { describe, it, expect, vi } from 'vitest'
import { createApp, defineComponent, h, nextTick, ref } from 'vue'

vi.mock('frappe-ui', async () => {
  const { defineComponent, h } = await import('vue')

  return {
    Tabs: defineComponent({
      props: {
        modelValue: { type: Number, default: 0 },
        tabs: { type: Array, default: () => [] },
      },
      emits: ['update:modelValue'],
      setup(props, { emit, slots }) {
        return () =>
          h('div', [
            h(
              'div',
              { role: 'tablist' },
              props.tabs.map((tab, index) =>
                h(
                  'button',
                  {
                    role: 'tab',
                    'aria-selected': props.modelValue === index,
                    onClick: () => emit('update:modelValue', index),
                  },
                  tab.label,
                ),
              ),
            ),
            h(
              'div',
              { role: 'tabpanel' },
              slots['tab-panel']?.({ tab: props.tabs[props.modelValue] }),
            ),
          ])
      },
    }),
  }
})

vi.mock('@/data/document', () => ({
  useDocument: () => ({
    document: {
      fieldPropertyOverrides: {},
    },
  }),
}))

vi.mock('@/components/FieldLayout/Section.vue', () => ({
  default: defineComponent({
    props: {
      section: { type: Object, required: true },
    },
    setup(props) {
      return () => h('section', props.section.label)
    },
  }),
}))

describe('FieldLayout tab state', () => {
  it('keeps the selected data field tab when the layout remounts', async () => {
    const { default: FieldLayout } = await import(
      '@/components/FieldLayout/FieldLayout.vue'
    )

    const root = document.createElement('div')
    document.body.appendChild(root)

    const Parent = defineComponent({
      setup() {
        const showLayout = ref(true)
        const fieldLayoutTabIndex = ref(0)
        const tabs = [
          {
            name: 'details_tab',
            label: 'Details',
            sections: [{ name: 'details_section', label: 'Details' }],
          },
          {
            name: 'data_tab',
            label: 'Data',
            sections: [{ name: 'data_section', label: 'Data' }],
          },
        ]

        return () =>
          h('div', [
            h(
              'button',
              {
                'data-testid': 'remount',
                onClick: async () => {
                  showLayout.value = false
                  await nextTick()
                  showLayout.value = true
                },
              },
              'Remount',
            ),
            showLayout.value &&
              h(FieldLayout, {
                tabs,
                data: {},
                doctype: 'CRM Deal',
                isGridRow: true,
                tabIndex: fieldLayoutTabIndex.value,
                'onUpdate:tabIndex': (value) => {
                  fieldLayoutTabIndex.value = value
                },
              }),
          ])
      },
    })

    const app = createApp(Parent)
    app.mount(root)

    root.querySelectorAll('[role="tab"]')[1].click()
    await nextTick()
    expect(root.querySelector('[aria-selected="true"]').textContent).toBe(
      'Data',
    )

    root.querySelector('[data-testid="remount"]').click()
    await nextTick()
    await nextTick()

    expect(root.querySelector('[aria-selected="true"]').textContent).toBe(
      'Data',
    )

    app.unmount()
    root.remove()
  })

  it('keeps the selected data field tab when DataFields remounts', async () => {
    const { default: FieldLayout } = await import(
      '@/components/FieldLayout/FieldLayout.vue'
    )

    const root = document.createElement('div')
    document.body.appendChild(root)

    const DataFieldsStub = defineComponent({
      props: {
        fieldLayoutTabIndex: { type: Number, default: 0 },
      },
      emits: ['update:fieldLayoutTabIndex'],
      setup(props, { emit }) {
        const tabs = [
          {
            name: 'details_tab',
            label: 'Details',
            sections: [{ name: 'details_section', label: 'Details' }],
          },
          {
            name: 'data_tab',
            label: 'Data',
            sections: [{ name: 'data_section', label: 'Data' }],
          },
        ]

        return () =>
          h(FieldLayout, {
            tabs,
            data: {},
            doctype: 'CRM Deal',
            isGridRow: true,
            tabIndex: props.fieldLayoutTabIndex,
            'onUpdate:tabIndex': (value) => {
              emit('update:fieldLayoutTabIndex', value)
            },
          })
      },
    })

    const Parent = defineComponent({
      setup() {
        const showDataFields = ref(true)
        const fieldLayoutTabIndex = ref(0)

        return () =>
          h('div', [
            h(
              'button',
              {
                'data-testid': 'remount-data-fields',
                onClick: async () => {
                  showDataFields.value = false
                  await nextTick()
                  showDataFields.value = true
                },
              },
              'Remount DataFields',
            ),
            showDataFields.value &&
              h(DataFieldsStub, {
                fieldLayoutTabIndex: fieldLayoutTabIndex.value,
                'onUpdate:fieldLayoutTabIndex': (value) => {
                  fieldLayoutTabIndex.value = value
                },
              }),
          ])
      },
    })

    const app = createApp(Parent)
    app.mount(root)

    root.querySelectorAll('[role="tab"]')[1].click()
    await nextTick()
    expect(root.querySelector('[aria-selected="true"]').textContent).toBe(
      'Data',
    )

    root.querySelector('[data-testid="remount-data-fields"]').click()
    await nextTick()
    await nextTick()

    expect(root.querySelector('[aria-selected="true"]').textContent).toBe(
      'Data',
    )

    app.unmount()
    root.remove()
  })

  it('keeps the selected tab by name when labels are duplicated and tabs reload', async () => {
    const { default: FieldLayout } = await import(
      '@/components/FieldLayout/FieldLayout.vue'
    )

    const root = document.createElement('div')
    document.body.appendChild(root)

    const Parent = defineComponent({
      setup() {
        const fieldLayoutTabIndex = ref(0)
        const fieldLayoutTabName = ref('')
        const tabs = ref([
          {
            name: 'tab_a',
            label: 'New Tab',
            sections: [{ name: 'section_a', label: 'First' }],
          },
          {
            name: 'tab_b',
            label: 'New Tab',
            sections: [{ name: 'section_b', label: 'Second' }],
          },
        ])

        return () =>
          h('div', [
            h(
              'button',
              {
                'data-testid': 'reload-tabs',
                onClick: () => {
                  tabs.value = [
                    {
                      name: 'tab_a',
                      label: 'New Tab',
                      sections: [{ name: 'section_a_new', label: 'First' }],
                    },
                    {
                      name: 'tab_b',
                      label: 'New Tab',
                      sections: [{ name: 'section_b_new', label: 'Second' }],
                    },
                  ]
                },
              },
              'Reload Tabs',
            ),
            h(FieldLayout, {
              tabs: tabs.value,
              data: {},
              doctype: 'CRM Deal',
              isGridRow: true,
              tabIndex: fieldLayoutTabIndex.value,
              tabName: fieldLayoutTabName.value,
              'onUpdate:tabIndex': (value) => {
                fieldLayoutTabIndex.value = value
              },
              'onUpdate:tabName': (value) => {
                fieldLayoutTabName.value = value
              },
            }),
          ])
      },
    })

    const app = createApp(Parent)
    app.mount(root)

    root.querySelectorAll('[role="tab"]')[1].click()
    await nextTick()
    expect(root.querySelector('[role="tabpanel"]').textContent).toBe('Second')

    root.querySelector('[data-testid="reload-tabs"]').click()
    await nextTick()

    expect(root.querySelector('[role="tabpanel"]').textContent).toBe('Second')

    app.unmount()
    root.remove()
  })

  it('restores the selected tab name from session storage after page remount', async () => {
    const { default: FieldLayout } = await import(
      '@/components/FieldLayout/FieldLayout.vue'
    )

    const root = document.createElement('div')
    document.body.appendChild(root)
    sessionStorage.clear()

    const DataFieldsStub = defineComponent({
      setup() {
        const doctype = 'CRM Deal'
        const docname = 'DEAL-001'
        const fieldLayoutTabIndex = ref(0)
        const fieldLayoutTabName = ref('')
        const storageKey = `fieldLayoutTab:${doctype}:${docname}`
        const tabs = [
          {
            name: 'tab_a',
            label: 'New Tab',
            sections: [{ name: 'section_a', label: 'First' }],
          },
          {
            name: 'tab_b',
            label: 'New Tab',
            sections: [{ name: 'section_b', label: 'Second' }],
          },
        ]

        const storedFieldLayoutTabName = sessionStorage.getItem(storageKey)
        if (storedFieldLayoutTabName) {
          fieldLayoutTabName.value = storedFieldLayoutTabName
        }

        return () =>
          h(FieldLayout, {
            tabs,
            data: {},
            doctype,
            isGridRow: true,
            tabIndex: fieldLayoutTabIndex.value,
            tabName: fieldLayoutTabName.value,
            'onUpdate:tabIndex': (value) => {
              fieldLayoutTabIndex.value = value
            },
            'onUpdate:tabName': (value) => {
              fieldLayoutTabName.value = value
              sessionStorage.setItem(storageKey, value)
            },
          })
      },
    })

    const Parent = defineComponent({
      setup() {
        const showPage = ref(true)

        return () =>
          h('div', [
            h(
              'button',
              {
                'data-testid': 'remount-page',
                onClick: async () => {
                  showPage.value = false
                  await nextTick()
                  showPage.value = true
                },
              },
              'Remount Page',
            ),
            showPage.value && h(DataFieldsStub),
          ])
      },
    })

    const app = createApp(Parent)
    app.mount(root)

    root.querySelectorAll('[role="tab"]')[1].click()
    await nextTick()
    expect(root.querySelector('[role="tabpanel"]').textContent).toBe('Second')

    root.querySelector('[data-testid="remount-page"]').click()
    await nextTick()
    await nextTick()

    expect(root.querySelector('[role="tabpanel"]').textContent).toBe('Second')

    app.unmount()
    root.remove()
    sessionStorage.clear()
  })
})
