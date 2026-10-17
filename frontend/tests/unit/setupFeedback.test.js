import { expect, it, vi } from 'vitest'
import { createApp, h, nextTick } from 'vue'

const capture = vi.hoisted(() => vi.fn())
vi.mock('@framework/ui/telemetry', () => ({
  useTelemetry: () => ({ capture }),
}))
vi.mock('frappe-ui', () => ({
  Button: {
    props: ['label', 'disabled'],
    setup:
      (props, { attrs }) =>
      () =>
        h('button', { ...attrs, disabled: props.disabled }, props.label),
  },
  Dialog: {
    props: ['open'],
    setup:
      (props, { slots }) =>
      () =>
        props.open ? h('div', [slots.default?.(), slots.actions?.()]) : null,
  },
  FormControl: { render: () => null },
}))
import SetupFeedback from '@/components/Setup/SetupFeedback.vue'
import { setupFeedback } from '@/composables/modals'

function mountFeedback() {
  setupFeedback.value = {
    skipped_setup: false,
    completed_steps: ['invite_team'],
  }
  const root = document.createElement('div')
  const app = createApp(SetupFeedback)
  app.config.globalProperties.__ = (text) => text
  app.mount(root)
  const button = (label) =>
    [...root.querySelectorAll('button')].find((b) => b.textContent === label)
  return { root, app, button }
}

it('sends feedback only after a rating is picked', async () => {
  const { root, app, button } = mountFeedback()
  try {
    expect(button('Send feedback').disabled).toBe(true)
    root.querySelector('[role="radio"]').click()
    await nextTick()
    button('Send feedback').click()
    expect(capture).toHaveBeenCalledWith('onboarding_feedback', {
      skipped_setup: false,
      completed_steps: ['invite_team'],
      rating: 1,
      comment: null,
    })
    expect(setupFeedback.value).toBe(null)
  } finally {
    app.unmount()
  }
})

it('closes without sending when dismissed', async () => {
  capture.mockClear()
  const { app, button } = mountFeedback()
  try {
    button('Not now').click()
    await nextTick()
    expect(capture).not.toHaveBeenCalled()
    expect(setupFeedback.value).toBe(null)
  } finally {
    app.unmount()
  }
})
