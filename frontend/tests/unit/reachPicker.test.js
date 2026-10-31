import { describe, expect, it, vi } from 'vitest'
import { createApp, defineComponent, h, nextTick } from 'vue'

// The desk resolves both at build time; here a stub stands in for each.
vi.mock('frappe/i18n', () => ({ __: (text) => text }))
vi.mock('frappe-ui', async () => {
  const { defineComponent, h } = await import('vue')
  return {
    Combobox: defineComponent({
      name: 'Combobox',
      props: ['modelValue', 'options'],
      emits: ['update:modelValue'],
      setup(props, { emit, expose }) {
        expose({ pick: (value) => emit('update:modelValue', value) })
        return () => h('div')
      },
    }),
  }
})

const { default: ReachPicker } =
  await import('../../../crm/fcrm/frontend/contact/ReachPicker.vue')

function fakePage() {
  return {
    docname: 'Walk 46019',
    isDirty: false,
    doc: {
      email_id: 'a@example.com',
      email_ids: [{ email_id: 'a@example.com' }, { email_id: 'b@example.com' }],
    },
    toast: { success: vi.fn(), error: vi.fn() },
    save: vi.fn(() => Promise.resolve()),
    call: vi.fn(() => Promise.resolve(true)),
    reload: vi.fn(() => Promise.resolve()),
  }
}

// Mounts the picker with the bindings the panel and the form give a field component.
function mountAsHost(page) {
  const host = { draft: vi.fn(), change: vi.fn() }
  let combobox
  const app = createApp(
    defineComponent({
      render: () =>
        h(ReachPicker, {
          page,
          field: { fieldname: 'email_id', label: 'Email Address' },
          modelValue: page.doc.email_id,
          'onUpdate:modelValue': host.draft,
          onChange: host.change,
          ref: (picker) => {
            combobox = picker?.$.subTree.component?.exposed
          },
        }),
    }),
  )
  app.mount(document.createElement('div'))
  return { host, combobox: () => combobox, app }
}

describe('ReachPicker', () => {
  it('sets the primary on the server and never writes the pick into the draft', async () => {
    const page = fakePage()
    const { host, combobox, app } = mountAsHost(page)
    await nextTick()

    combobox().pick('b@example.com')
    await vi.waitFor(() => expect(host.change).toHaveBeenCalled())

    expect(host.draft).not.toHaveBeenCalled()
    expect(page.call).toHaveBeenCalledWith('crm.api.contact.set_as_primary', {
      contact: 'Walk 46019',
      field: 'email',
      value: 'b@example.com',
    })
    expect(page.reload).toHaveBeenCalled()
    app.unmount()
  })

  it('writes nothing into the draft when the input is cleared', async () => {
    const page = fakePage()
    const { host, combobox, app } = mountAsHost(page)
    await nextTick()

    combobox().pick(null)
    await nextTick()

    expect(host.draft).not.toHaveBeenCalled()
    expect(page.call).not.toHaveBeenCalled()
    app.unmount()
  })
})
