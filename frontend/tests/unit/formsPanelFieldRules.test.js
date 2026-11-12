import { afterEach, describe, expect, it, vi } from 'vitest'
import { createApp, h, nextTick } from 'vue'

vi.mock('frappe-ui', async () => {
  const { defineComponent, h } = await import('vue')
  const stub = (name, render) =>
    defineComponent({
      name,
      props: ['label', 'modelValue', 'text'],
      setup:
        (props, { slots }) =>
        () =>
          render(props, slots),
    })
  const input = (name) =>
    stub(name, (props) => h('input', { value: props.modelValue }))
  return {
    Button: stub('Button', (props) => h('button', props.label)),
    Switch: stub('Switch', () => h('span')),
    TextInput: input('TextInput'),
    Textarea: input('Textarea'),
    Tooltip: stub('Tooltip', (props, slots) => slots.default?.()),
  }
})

const { default: PanelFieldSettings } = await import(
  '../../../crm/fcrm/frontend/forms/builder/PanelFieldSettings.vue'
)

let app
let root
afterEach(() => {
  app?.unmount()
  root?.remove()
})

async function mountPanel(rules) {
  root = document.createElement('div')
  document.body.append(root)
  const field = {
    fieldname: 'phone',
    label: 'Phone',
    fieldtype: 'Data',
    depends_on: '',
    mandatory_depends_on: '',
    read_only_depends_on: '',
    ...rules,
  }
  app = createApp({ render: () => h(PanelFieldSettings, { field }) })
  app.mount(root)
  await nextTick()
  return [...root.querySelectorAll('p')]
    .map((p) => p.textContent.trim())
    .filter((t) => t.startsWith('This rule does not work'))
}

describe('Field panel conditional rules', () => {
  it('shows why a rule does not work, under that rule', async () => {
    const errors = await mountPanel({
      mandatory_depends_on: 'eval:doc.qty >',
      read_only_depends_on: 'eval:window.x',
    })
    expect(errors).toEqual([
      'This rule does not work: unexpected token',
      'This rule does not work: unknown name: window',
    ])
  })

  it('shows no error for a rule that parses', async () => {
    const errors = await mountPanel({
      depends_on: 'eval:doc.email && doc.qty > 1',
      mandatory_depends_on: 'organization',
    })
    expect(errors).toEqual([])
  })
})
