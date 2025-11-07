import { createResource } from 'frappe-ui'
import { computed } from 'vue'

export function useDocumentPermissions(doctype, docname) {
  const permissions = createResource({
    url: 'frappe.client.get_doc_permissions',
    params: {
      doctype,
      docname,
    },
    auto: true,
    initialData: { permissions: {} },
  })
  const canDelete = computed(() => permissions.data?.permissions?.delete || false)


  return canDelete
}