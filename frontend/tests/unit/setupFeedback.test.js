import { expect, it, vi } from 'vitest'
import { createApp, h, nextTick, reactive } from 'vue'

const state = vi.hoisted(() => ({ telemetry: null }))
vi.mock('@framework/ui/telemetry', () => ({
  useTelemetry: () => state.telemetry,
}))
vi.mock('frappe-ui', () => ({
  Button: {
    props: ['label', 'disabled'],
    setup: (props, { attrs }) => () =>
      h('button', { ...attrs, disabled: props.disabled }, props.label),
  },
  FormControl: { render: () => null },
}))
import SetupFeedback from '@/components/Setup/SetupFeedback.vue'

function mountFeedback(enabled) {
  state.telemetry = reactive({ isEnabled: enabled })
  const root = document.createElement('div')
  const finish = vi.fn()
  const app = createApp(SetupFeedback, { onFinish: finish })
  app.config.globalProperties.__ = (text) => text
  app.mount(root)
  return { root, finish, app }
}

it('requires a rating only while telemetry is enabled', async () => {
  const { root, finish, app } = mountFeedback(true)
  try {
    const submit = root.querySelector('button:not([role="radio"])')
    expect(submit.disabled).toBe(true)
    expect(root.querySelector('[role="radiogroup"]').getAttribute('aria-required')).toBe('true')
    root.querySelector('[role="radio"]').click()
    await nextTick()
    expect(submit.disabled).toBe(false)
    submit.click()
    expect(finish).toHaveBeenCalledWith({ rating: 1, comment: null })
  } finally {
    app.unmount()
  }
})

it('allows unrated feedback after telemetry is disabled', async () => {
  const { root, finish, app } = mountFeedback(true)
  try {
    state.telemetry.isEnabled = false
    await nextTick()
    const submit = root.querySelector('button:not([role="radio"])')
    expect(submit.disabled).toBe(false)
    submit.click()
    expect(finish).toHaveBeenCalledWith({ rating: null, comment: null })
  } finally {
    app.unmount()
  }
})
