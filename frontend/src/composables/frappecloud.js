import { globalStore } from '@/stores/global'
import { createResource } from 'frappe-ui'
import { ref } from 'vue'

const baseEndpoint = ref('https://frappecloud.com')
const siteName = ref('')

export const currentSiteInfo = createResource({
  url: 'frappe.integrations.frappe_providers.frappecloud_billing.current_site_info',
  cache: 'currentSiteInfo',
  onSuccess: (data) => {
    baseEndpoint.value = data.base_url
    siteName.value = data.site_name
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
  window.open(
    `${baseEndpoint.value}/dashboard/sites/${siteName.value}`,
    '_blank',
  )
}
