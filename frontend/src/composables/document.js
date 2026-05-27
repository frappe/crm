import { ref } from 'vue'
import { call, toast } from 'frappe-ui'

export const showCreateDocumentModal = ref(false)
export const createDocumentDoctype = ref('')
export const createDocumentData = ref({})
export const createDocumentCallback = ref(null)

let erpnextEnabledCache = null

async function isERPNextSyncEnabled() {
  if (erpnextEnabledCache !== null) return erpnextEnabledCache
  try {
    const enabled = await call('frappe.client.get_single_value', {
      doctype: 'ERPNext CRM Settings',
      field: 'enabled',
    })
    erpnextEnabledCache = !!enabled
  } catch {
    erpnextEnabledCache = false
  }
  return erpnextEnabledCache
}

export async function createDocument(doctype, obj, close, callback) {
  if (!doctype) return
  if (doctype === 'CRM Product' && (await isERPNextSyncEnabled())) {
    close?.()
    toast.info(__('Create products as Items in ERPNext'))
    window.open('/app/item/new', '_blank')
    return
  }
  close?.()
  createDocumentDoctype.value = doctype
  createDocumentData.value = obj || {}
  createDocumentCallback.value = callback || null
  showCreateDocumentModal.value = true
}
