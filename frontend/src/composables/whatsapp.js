import { createResource } from 'frappe-ui'
import { ref } from 'vue'

export const whatsappEnabled = ref(false)
export const isWhatsAppInstalled = ref(false)

createResource({
  url: 'crm.api.whatsapp.is_whatsapp_enabled',
  cache: 'Is WhatsApp Enabled',
  auto: true,
  onSuccess: (data) => {
    whatsappEnabled.value = Boolean(data)
  },
})

createResource({
  url: 'crm.api.whatsapp.is_whatsapp_installed',
  cache: 'Is WhatsApp Installed',
  auto: true,
  onSuccess: (data) => {
    isWhatsAppInstalled.value = Boolean(data)
  },
})

// Meta's review outcome for a template, as a Badge theme.
const TEMPLATE_STATUS_THEMES = {
  Approved: 'green',
  Pending: 'orange',
  Rejected: 'red',
  Deleted: 'gray',
}

export function templateStatusTheme(status) {
  return TEMPLATE_STATUS_THEMES[status] || 'gray'
}
