import { call } from 'frappe-ui'

let isERPNextEnabled = null

export async function checkERPNextEnabled() {
  if (isERPNextEnabled === null) {
    try {
      const result = await call('frappe.client.get_single_value', {
        doctype: 'ERPNext CRM Settings',
        field: 'enabled'
      })
      isERPNextEnabled = !!result
    } catch (error) {
      isERPNextEnabled = false
    }
  }
  return isERPNextEnabled
}

export function resetERPNextCheck() {
  isERPNextEnabled = null
}
