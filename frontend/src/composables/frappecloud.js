import { globalStore } from '@/stores/global'
import { createResource } from 'frappe-ui'
import { ref } from 'vue'

const baseEndpoint = ref('https://frappecloud.com')
const isPaymentModeAdded = ref(false)

export const currentSiteInfo = createResource({
  url: 'frappe.integrations.frappe_providers.frappecloud_billing.current_site_info',
  cache: 'currentSiteInfo',
  onSuccess: (data) => {
    isPaymentModeAdded.value = data.is_payment_method_added
    baseEndpoint.value = data.base_url
  },
})

export const confirmLoginToFrappeCloud = () => {
  currentSiteInfo.fetch()

  const { $dialog } = globalStore()

  $dialog({
    title: __('Login to Frappe Cloud?'),
    message: __(
      'Are you sure you want to login to your Frappe Cloud dashboard?',
    ),
    actions: [
      {
        label: __('Confirm'),
        variant: 'solid',
        onClick(close) {
          loginToFrappeCloud()
          close()
        },
      },
    ],
  })
}

const loginToFrappeCloud = () => {
  let redirectRoute = ''

  if (isPaymentModeAdded.value) {
    redirectRoute = '/dashboard'
  } else {
    redirectRoute = '/dashboard/welcome'
  }

  window.open(`${baseEndpoint.value}${redirectRoute}`, '_blank')
}
