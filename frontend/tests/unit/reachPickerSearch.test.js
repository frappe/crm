import { describe, expect, it, vi } from 'vitest'
import { createApp, h, nextTick } from 'vue'

// The real Combobox, since the bug lives in how it fills its search; frappe-ui's index does not load under vitest.
vi.mock('frappe-ui', async () => ({
  Combobox: (
    await import(
      '../../node_modules/frappe-ui/src/components/Combobox/Combobox.vue'
    )
  ).default,
}))

const { default: ReachPicker } = await import(
  '../../../crm/fcrm/frontend/contact/ReachPicker.vue'
)

function fakePage() {
  return {
    docname: 'Walk 46047',
    doc: {
      email_id: 'a@example.com',
      email_ids: [{ email_id: 'a@example.com' }, { email_id: 'b@example.com' }],
    },
  }
}

function mountPicker(page) {
  const root = document.createElement('div')
  document.body.appendChild(root)
  const app = createApp({
    render: () =>
      h(ReachPicker, {
        page,
        field: { fieldname: 'email_id', label: 'Email Address' },
        modelValue: page.doc.email_id,
      }),
  })
  app.mount(root)
  return {
    input: root.querySelector('input'),
    unmount: () => {
      app.unmount()
      root.remove()
    },
  }
}

async function settle() {
  for (let i = 0; i < 5; i++) await nextTick()
}

async function type(input, value) {
  input.value = value
  input.dispatchEvent(new Event('input', { bubbles: true }))
  await settle()
}

function addRows() {
  return [...document.body.querySelectorAll('[role="option"]')]
    .map((option) => option.textContent.trim())
    .filter((text) => text.startsWith('Add '))
}

describe('ReachPicker search', () => {
  it('shows the primary while closed', async () => {
    const { input, unmount } = mountPicker(fakePage())
    await settle()

    expect(input.value).toBe('a@example.com')
    unmount()
  })

  it('opens with an empty search, so a typed value is offered alone', async () => {
    const { input, unmount } = mountPicker(fakePage())
    await settle()

    input.focus()
    await settle()
    expect(input.value).toBe('')

    await type(input, 'new@example.com')
    expect(addRows()).toEqual(['Add new@example.com'])
    unmount()
  })
})
