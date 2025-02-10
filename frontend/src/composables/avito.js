import { createResource } from 'frappe-ui'
import { ref } from 'vue'

export const avitoEnabled = ref(false)
export const isAvitoInstalled = ref(false)
createResource({
  url: 'crm.api.avito.is_avito_enabled',
  cache: 'Is Avito Enabled',
  auto: true,
  onSuccess: (data) => {
    avitoEnabled.value = Boolean(data)
  },
})
createResource({
  url: 'crm.api.avito.is_avito_installed',
  cache: 'Is Avito Installed',
  auto: true,
  onSuccess: (data) => {
    isAvitoInstalled.value = Boolean(data)
  },
})
