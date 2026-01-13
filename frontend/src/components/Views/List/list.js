import { useList as _useList } from 'frappe-ui'
import { computed, inject } from 'vue'

const listCache = {}

export function useList() {
  const doctype = inject('doctype')
  const viewName = inject('viewName')
  const currentView = inject('currentView')

  const fields = () => currentView.value?.columns?.map((col) => col.key) || []
  const filters = () => currentView.value?.filters || {}
  const orderBy = () => currentView.value?.order_by || 'modified asc'

  if (!listCache[doctype]?.[viewName]) {
    if (!listCache[doctype]) {
      listCache[doctype] = {}
    }
    listCache[doctype][viewName] = _useList({
      doctype,
      fields,
      filters,
      orderBy,
      start: 0,
      limit: 20,
      immediate: false,
    })
  }

  const columns = computed(() => {
    return currentView.value?.columns || []
  })

  const rows = computed(() => {
    return listCache[doctype][viewName]?.data || []
  })

  function reload() {
    if (listCache[doctype][viewName].isFetching) return
    listCache[doctype][viewName].reload()
  }

  return {
    list: listCache[doctype][viewName],
    columns,
    rows,
    reload,
  }
}
