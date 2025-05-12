import { ref } from 'vue'

export const showCreateDocumentModal = ref(false)
export const createDocumentDoctype = ref('')
export const createDocumentData = ref({})

export function createDocument(doctype, obj, close) {
  if (doctype) {
    close()
    createDocumentDoctype.value = doctype
    createDocumentData.value = obj || {}
    showCreateDocumentModal.value = true
  }
}
