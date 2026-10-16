import { expect, it, vi } from 'vitest'
import { createApp, h, nextTick } from 'vue'

const mocks = vi.hoisted(() => ({ call: vi.fn(), disable: vi.fn() }))
vi.mock('@framework/ui/telemetry', () => ({
  useTelemetry: () => ({ disable: mocks.disable }),
}))
vi.mock('frappe-ui', () => ({
  call: mocks.call,
  Button: {
    props: ['label', 'disabled'],
    setup: (props, { attrs }) => () =>
      h('button', { ...attrs, disabled: props.disabled }, props.label),
  },
  ErrorMessage: {
    props: ['message'],
    setup: (props) => () => h('p', props.message),
  },
}))
import SetupTelemetryConsent from '@/components/Setup/SetupTelemetryConsent.vue'

async function mountConsent(enabled = 1) {
  mocks.call.mockReset().mockResolvedValue(enabled)
  mocks.disable.mockClear()
  const root = document.createElement('div')
  const accepted = vi.fn()
  const declined = vi.fn()
  const app = createApp(SetupTelemetryConsent, { onAccepted: accepted, onDeclined: declined })
  app.config.globalProperties.__ = (text) => text
  app.mount(root)
  await settle()
  return { root, app, accepted, declined }
}

async function settle() {
  await Promise.resolve()
  await nextTick()
}

it('keeps telemetry unchanged when the user agrees', async () => {
  const { root, app, accepted, declined } = await mountConsent()
  try {
    root.querySelectorAll('button')[1].click()
    expect(accepted).toHaveBeenCalledOnce()
    expect(declined).not.toHaveBeenCalled()
    expect(mocks.call).toHaveBeenCalledTimes(1)
    expect(mocks.disable).not.toHaveBeenCalled()
  } finally { app.unmount() }
})

it('persists opt-out before disabling telemetry and leaving', async () => {
  const { root, app, declined } = await mountConsent()
  try {
    root.querySelector('button').click()
    expect(declined).not.toHaveBeenCalled()
    await settle()
    expect(mocks.call).toHaveBeenLastCalledWith('frappe.client.set_value', {
      doctype: 'System Settings', name: 'System Settings',
      fieldname: 'enable_telemetry', value: 0,
    })
    expect(mocks.disable).toHaveBeenCalledOnce()
    expect(declined).toHaveBeenCalledOnce()
  } finally { app.unmount() }
})

it('respects a site that already opted out', async () => {
  const { app, declined } = await mountConsent(0)
  try {
    expect(declined).toHaveBeenCalledOnce()
    expect(mocks.disable).toHaveBeenCalledOnce()
    expect(mocks.call).toHaveBeenCalledTimes(1)
  } finally { app.unmount() }
})

it('stays on the choice when saving fails', async () => {
  const { root, app, declined } = await mountConsent()
  const log = vi.spyOn(console, 'error').mockImplementation(() => {})
  try {
    mocks.call.mockRejectedValueOnce(new Error('Unable to save'))
    root.querySelector('button').click()
    await settle()
    expect(root.textContent).toContain('Could not save your preference')
    expect(declined).not.toHaveBeenCalled()
    expect(mocks.disable).not.toHaveBeenCalled()
  } finally { app.unmount(); log.mockRestore() }
})
