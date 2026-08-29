import { call } from 'frappe-ui'
import { sessionStore } from '@/stores/session'

export function useVisitedRecords(doctype: string) {
  const { user } = sessionStore()

  function isVisited(seen?: string | string[] | null) {
    if (!seen) return false
    const seenBy = typeof seen === 'string' ? JSON.parse(seen) : seen
    return seenBy.includes(user)
  }

  function markVisited(name?: string) {
    if (!name) return
    call('crm.api.doc.add_seen', { doctype, name })
  }

  return { isVisited, markVisited }
}
