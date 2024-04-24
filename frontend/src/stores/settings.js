import { createResource } from 'frappe-ui'
import { ref } from 'vue'

export const whatsappEnabled = ref(false)

createResource({
  url: 'crm.api.whatsapp.is_whatsapp_enabled',
  cache: 'Is Whatsapp Enabled',
  auto: true,
  onSuccess: (data) => {
    whatsappEnabled.value = data
  },
})