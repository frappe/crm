import { createResource } from 'frappe-ui'
import { computed, ref } from 'vue'

const windowWidth = ref(window.innerWidth)

function handleResize() {
  windowWidth.value = window.innerWidth
}

window.addEventListener('resize', handleResize)

export const whatsappEnabled = ref(false)
export const isWhatsappInstalled = ref(false)
createResource({
  url: 'crm.api.whatsapp.is_whatsapp_enabled',
  cache: 'Is Whatsapp Enabled',
  auto: true,
  onSuccess: (data) => {
    whatsappEnabled.value = Boolean(data)
  },
})
createResource({
  url: 'crm.api.whatsapp.is_whatsapp_installed',
  cache: 'Is Whatsapp Installed',
  auto: true,
  onSuccess: (data) => {
    isWhatsappInstalled.value = Boolean(data)
  },
})

export const callEnabled = ref(false)
export const twilioEnabled = ref(false)
export const exotelEnabled = ref(false)
export const defaultCallingMedium = ref('')
createResource({
  url: 'crm.integrations.api.is_call_integration_enabled',
  cache: 'Is Call Integration Enabled',
  auto: true,
  onSuccess: (data) => {
    twilioEnabled.value = Boolean(data.twilio_enabled)
    exotelEnabled.value = Boolean(data.exotel_enabled)
    defaultCallingMedium.value = data.default_calling_medium
    callEnabled.value = twilioEnabled.value || exotelEnabled.value
  },
})

export const mobileSidebarOpened = ref(false)

export const isMobileView = computed(() => windowWidth.value < 768)

export const showSettings = ref(false)

export const disableSettingModalOutsideClick = ref(false)

export const activeSettingsPage = ref('')
