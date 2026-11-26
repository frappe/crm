import { call, createResource } from 'frappe-ui'
import { reactive, ref } from 'vue'

export const whatsappEnabled = ref(false)
export const isWhatsAppInstalled = ref(false)

// The user's DocType-level permissions on WA Flow; Sales roles get read only.
export const flowPermissions = reactive({ read: false, write: false })

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
    if (data) loadFlowPermissions()
  },
})

async function loadFlowPermissions() {
  const [read, write] = await Promise.all(
    ['read', 'write'].map((perm_type) =>
      call('frappe.client.has_permission', {
        doctype: 'WA Flow',
        docname: '',
        perm_type,
      }),
    ),
  )
  Object.assign(flowPermissions, {
    read: read.has_permission,
    write: write.has_permission,
  })
}

// Meta's review outcome for a template, as a Badge theme.
const TEMPLATE_STATUS_THEMES = {
  Approved: 'green',
  Pending: 'amber',
  Rejected: 'red',
  Deleted: 'gray',
}

export function templateStatusTheme(status) {
  return TEMPLATE_STATUS_THEMES[status] || 'gray'
}
