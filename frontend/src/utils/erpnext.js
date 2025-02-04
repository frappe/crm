import { call } from 'frappe-ui'

export async function checkERPNextEnabled() {
  try {
    return await call('frappe.client.get_single_value', {
      doctype: 'ERPNext CRM Settings',
      field: 'enabled'
    })
  } catch (error) {
    return false;
  }
}

