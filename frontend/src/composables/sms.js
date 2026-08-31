import { createResource } from 'frappe-ui'
import { ref } from 'vue'

export const smsEnabled = ref(false)

createResource({
  url: 'crm.api.sms.is_sms_enabled',
  cache: 'Is SMS Enabled',
  auto: true,
  onSuccess: (data) => {
    smsEnabled.value = Boolean(data)
  },
})
