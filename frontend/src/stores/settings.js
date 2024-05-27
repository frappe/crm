import { createResource } from 'frappe-ui'
import { useScreenSize } from '@/composables'
import { computed, ref } from 'vue'

export const whatsappEnabled = ref(false)
createResource({
  url: 'crm.api.whatsapp.is_whatsapp_enabled',
  cache: 'Is Whatsapp Enabled',
  auto: true,
  onSuccess: (data) => {
    whatsappEnabled.value = Boolean(data)
  },
})
export const callEnabled = ref(false)
createResource({
  url: 'crm.integrations.twilio.api.is_enabled',
  cache: 'Is Twilio Enabled',
  auto: true,
  onSuccess: (data) => {
    callEnabled.value = Boolean(data)
  },
})

export const mobileSidebarOpened = ref(false)

const screenSize = useScreenSize()
export const isMobileView = computed(() => screenSize.width < 768)
