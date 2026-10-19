import { expect, it, vi } from 'vitest'
import { createApp, h, nextTick, ref } from 'vue'

vi.mock('frappe-ui', () => ({ Progress: { render: () => null } }))
import Stepper from '@/components/Stepper/Stepper.vue'

function mountStepper(selectable, vertical = false) {
  const current = ref('feedback')
  const steps = ['email', 'leads', 'team', 'about', 'feedback'].map(
    (value) => ({
      value,
      label: value,
      selectable,
    }),
  )
  const root = document.createElement('div')
  const app = createApp({
    setup: () => () =>
      h(Stepper, {
        steps,
        vertical,
        clickable: true,
        modelValue: current.value,
        'onUpdate:modelValue': (value) => {
          current.value = value
        },
      }),
  })
  app.config.globalProperties.__ = (text) => text
  app.mount(root)
  return { root, app, current }
}

for (const vertical of [false, true]) {
  it(`allows returning from the first to a reached last step, vertical=${vertical}`, async () => {
    const { root, app, current } = mountStepper(true, vertical)
    try {
      const button = (name) =>
        [...root.querySelectorAll('button')].find((element) =>
          element.textContent.includes(name),
        )
      button('email').click()
      await nextTick()
      expect(current.value).toBe('email')
      expect(button('feedback')).toBeDefined()
      button('feedback').click()
      await nextTick()
      expect(current.value).toBe('feedback')
    } finally {
      app.unmount()
    }
  })
}

it('keeps unreached future steps unavailable by default', async () => {
  const { root, app, current } = mountStepper(undefined)
  try {
    root.querySelector('button').click()
    await nextTick()
    expect(current.value).toBe('email')
    expect(root.querySelectorAll('button')).toHaveLength(0)
  } finally {
    app.unmount()
  }
})
