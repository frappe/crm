import { createResource } from 'frappe-ui'
import { computed, ref } from 'vue'

const store = {}

export function useViews(doctype) {
  if (!store[doctype]) {
    store[doctype] = createState(doctype)
  }
  return store[doctype]
}

function createState(doctype) {
  const views = ref([])

  const currentView = computed(() => {
    if (!views.value.length) return null
    return views.value.find((v) => v.is_default) || null
  })

  createResource({
    url: 'crm.api.views.get_doctype_views',
    params: { doctype: doctype || '' },
    cache: 'CRM Views',
    auto: true,
    transform(_views) {
      _views.forEach((view) => {
        view.columns = JSON.parse(view.columns || '[]')
        view.rows = JSON.parse(view.rows || '[]')
      })
      views.value = _views
      return _views
    },
  })

  return {
    views,
    currentView,
  }
}
