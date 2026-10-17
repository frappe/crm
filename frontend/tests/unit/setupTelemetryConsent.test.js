import { expect, it, vi } from 'vitest'
import { createApp, h, nextTick } from 'vue'

const mocks = vi.hoisted(() => ({ call: vi.fn(), disable: vi.fn(), install: vi.fn() }))
vi.mock('@framework/ui/telemetry', () => ({
  useTelemetry: () => ({ disable: mocks.disable }),
  telemetryPlugin: { install: mocks.install },
}))
vi.mock('frappe-ui', () => ({
  call: mocks.call,
  Checkbox: {
    props: ['modelValue', 'disabled', 'label'],
    emits: ['update:modelValue'],
    setup: (props, { emit }) => () => h('label', [
      h('input', { type: 'checkbox', checked: props.modelValue, disabled: props.disabled,
        onChange: (event) => emit('update:modelValue', event.target.checked) }), props.label,
    ]),
  },
  ErrorMessage: { props: ['message'], setup: (props) => () => h('p', props.message) },
}))
import SetupTelemetryConsent from '@/components/Setup/SetupTelemetryConsent.vue'

function mountPreference() {
  mocks.call.mockReset().mockResolvedValue()
  mocks.disable.mockClear()
  mocks.install.mockReset().mockResolvedValue()
  const root = document.createElement('div')
  const app = createApp(SetupTelemetryConsent)
  app.config.globalProperties.__ = (text) => text
  app.mount(root)
  return { root, app, checkbox: root.querySelector('input') }
}

async function settle() {
  await Promise.resolve()
  await Promise.resolve()
  await Promise.resolve()
  await nextTick()
}

it('shows a checked usage-data checkbox without a separate consent screen', () => {
  const { root, app, checkbox } = mountPreference()
  try {
    expect(checkbox.checked).toBe(true)
    expect(root.textContent).toContain('Share usage data')
    expect(mocks.call).not.toHaveBeenCalled()
  } finally { app.unmount() }
})

it('saves opt-out and stops telemetry without navigating away', async () => {
  const { app, checkbox } = mountPreference()
  try {
    checkbox.checked = !checkbox.checked
    checkbox.dispatchEvent(new Event('change'))
    await settle()
    expect(mocks.call).toHaveBeenCalledWith('frappe.client.set_value', {
      doctype: 'System Settings', name: 'System Settings',
      fieldname: 'enable_telemetry', value: 0,
    })
    expect(mocks.disable).toHaveBeenCalledOnce()
    expect(checkbox.checked).toBe(false)
    checkbox.checked = !checkbox.checked
    checkbox.dispatchEvent(new Event('change'))
    await settle()
    expect(mocks.install).toHaveBeenCalledOnce()
    expect(checkbox.checked).toBe(true)
  } finally { app.unmount() }
})

it('keeps the saved preference when updating fails', async () => {
  const { root, app, checkbox } = mountPreference()
  const log = vi.spyOn(console, 'error').mockImplementation(() => {})
  try {
    mocks.call.mockRejectedValueOnce(new Error('Unable to save'))
    checkbox.checked = !checkbox.checked
    checkbox.dispatchEvent(new Event('change'))
    await settle()
    expect(root.textContent).toContain('Could not save your preference')
    expect(mocks.disable).not.toHaveBeenCalled()
  } finally { app.unmount(); log.mockRestore() }
})
