import { closeCloudSettings, openCloudSettings } from '@frappe/cloud-sdk'
import { toast } from 'frappe-ui'
import { onUnmounted, ref } from 'vue'

// True while the Cloud Settings dialog is on screen
export const cloudSettingsOpen = ref(false)

let dialogOwner = null

// Frappe marks cloud_settings enabled only for System Managers on a Frappe Cloud v2 site
export const isCloudSettingsAvailable = () =>
  window.cloud_settings?.enabled === true

export async function openBillingDialog() {
  cloudSettingsOpen.value = true
  try {
    await openCloudSettings({
      panels: ['billing', 'marketplace', 'domains', 'advanced'],
      tab: 'billing',
      theme: 'auto',
      onClose: () => (cloudSettingsOpen.value = false),
    })
  } catch (error) {
    cloudSettingsOpen.value = false
    throw error
  }
}

export function useCloudSettings() {
  const opening = ref(false)
  const consumer = Symbol()

  // Only the consumer that last opened the dialog takes it down on unmount
  onUnmounted(() => {
    if (dialogOwner !== consumer) return
    dialogOwner = null
    closeCloudSettings()
    cloudSettingsOpen.value = false
  })

  async function open() {
    if (opening.value) return
    dialogOwner = consumer
    opening.value = true
    try {
      await openBillingDialog()
    } catch (error) {
      toast.error(error?.message || __('Could not open Cloud Settings'))
    } finally {
      opening.value = false
    }
  }

  return { available: isCloudSettingsAvailable(), opening, open }
}
