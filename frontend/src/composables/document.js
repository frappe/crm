import { ref } from 'vue'

export const showCreateDocumentModal = ref(false)
export const createDocumentDoctype = ref('')
export const createDocumentData = ref({})
export const createDocumentCallback = ref(null)

export function createDocument(doctype, obj, close, callback) {
  if (doctype) {
    close?.()
    createDocumentDoctype.value = doctype
    createDocumentData.value = obj || {}
    createDocumentCallback.value = callback || null
    showCreateDocumentModal.value = true
  }
}
