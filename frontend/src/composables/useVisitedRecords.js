import { call } from 'frappe-ui'
import { sessionStore } from '@/stores/session'

export function useVisitedRecords(doctype) {
  const { user } = sessionStore()

  function isVisited(seen) {
    if (!seen) return false
    let seenBy = typeof seen === 'string' ? JSON.parse(seen) : seen
    return seenBy.includes(user)
  }

  function markVisited(name) {
    if (!name) return
    call('crm.api.doc.add_seen', { doctype, name })
  }

  return { isVisited, markVisited }
}
