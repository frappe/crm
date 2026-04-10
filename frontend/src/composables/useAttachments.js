import { createResource } from 'frappe-ui'

const pendingDeletionsMap = new Map()

export function useAttachments(doctype, docname) {
  const key = `${doctype}::${docname}`
  if (!pendingDeletionsMap.has(key)) {
    pendingDeletionsMap.set(key, new Set())
  }
  const pending = pendingDeletionsMap.get(key)

  function trackOldFile(oldValue, newValue) {
    if (isFileUrl(oldValue) && oldValue !== newValue) {
      pending.add(oldValue)
    }
  }

  function processPendingDeletions() {
    if (!pending.size) return
    pending.forEach((file_url) => deleteFileRecord(doctype, docname, file_url))
    pending.clear()
    pendingDeletionsMap.delete(key)
  }

  return { trackOldFile, processPendingDeletions }
}

export function isFileUrl(v) {
  return (
    typeof v === 'string' &&
    (v.startsWith('/files/') || v.startsWith('/private/files/'))
  )
}

function deleteFileRecord(doctype, docname, file_url) {
  createResource({
    url: 'crm.api.delete_attachment',
    params: { doctype, docname, file_url },
    auto: true,
    onError: (e) => console.error('Failed to delete file attachment', e),
  })
}
