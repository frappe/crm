import { afterEach, describe, expect, it, vi } from 'vitest'
import { createApp, h, nextTick } from 'vue'

vi.mock('frappe-ui', async () => {
  const { defineComponent, h } = await import('vue')
  const stub = (name, render) =>
    defineComponent({
      name,
      props: ['label', 'message', 'modelValue', 'text'],
      setup:
        (props, { slots }) =>
        () =>
          render(props, slots),
    })
  return {
    Button: stub('Button', (props) => h('button', props.label)),
    ErrorMessage: stub('ErrorMessage', (props) =>
      h('p', { 'data-error': '' }, props.message),
    ),
    FormControl: stub('FormControl', (props) =>
      h('label', [props.label, h('input', { value: props.modelValue })]),
    ),
    Switch: stub('Switch', () => h('span')),
    Tooltip: stub('Tooltip', (props, slots) => slots.default?.()),
  }
})

const { default: FieldCard } = await import(
  '../../../crm/fcrm/frontend/settings/forms/FieldCard.vue'
)

let app
let root
afterEach(() => {
  app?.unmount()
  root?.remove()
})

async function mountCard(rules) {
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
  app = createApp({ render: () => h(FieldCard, { field, expanded: true }) })
  app.mount(root)
  await nextTick()
  return [...root.querySelectorAll('[data-error]')].map((p) => p.textContent)
}

describe('FieldCard conditional rules', () => {
  it('shows why a rule does not work, under that rule', async () => {
    const errors = await mountCard({
      mandatory_depends_on: 'eval:doc.qty >',
      read_only_depends_on: 'eval:window.x',
    })
    expect(errors).toEqual([
      'This rule does not work: unexpected token',
      'This rule does not work: unknown name: window',
    ])
  })

  it('shows no error for a rule that parses', async () => {
    const errors = await mountCard({
      depends_on: 'eval:doc.email && doc.qty > 1',
      mandatory_depends_on: 'organization',
    })
    expect(errors).toEqual([])
  })
})
