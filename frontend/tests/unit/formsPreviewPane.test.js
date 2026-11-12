import { afterEach, describe, expect, it, vi } from 'vitest'
import { createApp, h, nextTick, reactive } from 'vue'

vi.mock('frappe-ui', async () => {
  const { defineComponent, h } = await import('vue')
  const stub = (name, render) =>
    defineComponent({
      name,
      props: ['label', 'modelValue'],
      setup:
        (props, { slots }) =>
        () =>
          render(props, slots),
    })
  return {
    Button: stub('Button', (props, slots) =>
      h('button', props.label ?? slots.default?.()),
    ),
    FormControl: stub('FormControl', (props) => h('label', props.label)),
  }
})

const { default: PreviewPane } = await import(
  '../../../crm/fcrm/frontend/forms/builder/PreviewPane.vue'
)

let app
let root
afterEach(() => {
  app?.unmount()
  root?.remove()
})

async function submitPreview(formFields) {
  root = document.createElement('div')
  document.body.append(root)
  const form = reactive({
    title: 'Contact us',
    fields: [],
    success_message: '',
    ...formFields,
  })
  const draft = { form, linkMeta: reactive({}) }
  app = createApp({ render: () => h(PreviewPane, { draft }) })
  app.mount(root)
  await nextTick()
  const submit = [...root.querySelectorAll('button')].find(
    (b) => b.textContent === 'Submit',
  )
  submit.click()
  await nextTick()
  return root.textContent
}

describe('PreviewPane success screen', () => {
  it('shows the message after a submit', async () => {
    const text = await submitPreview({ success_message: 'We will call you.' })
    expect(text).toContain('We will call you.')
  })

  it('falls back to "Thank you!" without a message', async () => {
    expect(await submitPreview({})).toContain('Thank you!')
  })

  it('says where visitors go when After submit is a URL', async () => {
    const text = await submitPreview({
      after_submit: 'url',
      redirect_url: ' https://example.com/thanks ',
      success_message: 'We will call you.',
    })
    expect(text).toContain('Visitors go to https://example.com/thanks')
    expect(text).not.toContain('We will call you.')
  })

  it('shows the message when After submit is a URL but the URL is empty', async () => {
    const text = await submitPreview({
      after_submit: 'url',
      redirect_url: '  ',
      success_message: 'We will call you.',
    })
    expect(text).toContain('We will call you.')
  })

  it('ignores a stale URL when After submit shows the message', async () => {
    const text = await submitPreview({
      after_submit: 'message',
      redirect_url: 'https://example.com/thanks',
      success_message: 'We will call you.',
    })
    expect(text).toContain('We will call you.')
    expect(text).not.toContain('Visitors go to')
  })
})
