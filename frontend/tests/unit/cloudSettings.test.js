import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

const sdk = vi.hoisted(() => ({ open: vi.fn(), close: vi.fn() }))
vi.mock('@frappe/cloud-sdk', () => ({
  openCloudSettings: sdk.open,
  closeCloudSettings: sdk.close,
}))
vi.mock('frappe-ui', () => ({ toast: { error: vi.fn() } }))

import {
  cloudSettingsOpen,
  isCloudSettingsAvailable,
  openBillingDialog,
} from '@/composables/cloudSettings'

beforeEach(() => {
  vi.resetAllMocks()
  sdk.open.mockResolvedValue(undefined)
  cloudSettingsOpen.value = false
  window.cloud_settings = { enabled: true }
})

afterEach(() => {
  delete window.cloud_settings
})

describe('isCloudSettingsAvailable', () => {
  it('reads the boot flag Frappe sets on a pilot-managed site', () => {
    expect(isCloudSettingsAvailable()).toBe(true)
    window.cloud_settings.enabled = false
    expect(isCloudSettingsAvailable()).toBe(false)
  })

  it('is false on a Frappe version that has no cloud_settings in boot', () => {
    delete window.cloud_settings
    expect(isCloudSettingsAvailable()).toBe(false)
  })
})

describe('openBillingDialog', () => {
  it('opens on the billing panel and stays open until the dialog closes', async () => {
    await openBillingDialog()
    expect(sdk.open).toHaveBeenCalledOnce()
    const options = sdk.open.mock.calls[0][0]
    expect(options).toMatchObject({
      panels: ['billing', 'marketplace', 'domains', 'advanced'],
      tab: 'billing',
    })
    expect(cloudSettingsOpen.value).toBe(true)
    options.onClose()
    expect(cloudSettingsOpen.value).toBe(false)
  })

  it('resets and rethrows when the dialog fails to open', async () => {
    const error = new Error('Could not reach Cloud Settings')
    sdk.open.mockRejectedValue(error)
    await expect(openBillingDialog()).rejects.toThrow(error)
    expect(cloudSettingsOpen.value).toBe(false)
  })
})
