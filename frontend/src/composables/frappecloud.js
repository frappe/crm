import { globalStore } from '@/stores/global'
import { call } from 'frappe-ui'

const frappeCloudBaseEndpoint = 'https://frappecloud.com'

export const confirmLoginToFrappeCloud = () => {
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
  call(
    'frappe.integrations.frappe_providers.frappecloud_billing.current_site_info',
  ).then((response) => {
    if (!response) return

    let redirectRoute = ''

    if (response.is_payment_method_added) {
      redirectRoute = '/dashboard'
    } else {
      redirectRoute = '/dashboard/welcome'
    }

    window.open(`${frappeCloudBaseEndpoint}${redirectRoute}`, '_blank')
  })
}
