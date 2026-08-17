import { useStorage } from '@vueuse/core'

const MAX_VISITED_RECORDS = 1000

export function useVisitedRecords(doctype) {
  const visitedRecords = useStorage(`visitedRecords:${doctype}`, [])

  function isVisited(name) {
    return visitedRecords.value.includes(name)
  }

  function markVisited(name) {
    if (!name || isVisited(name)) return
    visitedRecords.value.push(name)
    if (visitedRecords.value.length > MAX_VISITED_RECORDS) {
      visitedRecords.value.splice(
        0,
        visitedRecords.value.length - MAX_VISITED_RECORDS,
      )
    }
  }

  return { isVisited, markVisited }
}
