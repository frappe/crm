import { createResource } from 'frappe-ui'
import { reactive, watch, toRefs } from 'vue'

const views = reactive({})

export function useViews(doctype) {
  if (!views[doctype]) {
    const resource = createResource({
      url: 'crm.api.views.get_doctype_views',
      params: { doctype: doctype || '' },
      cache: 'CRM Views' + doctype,
      auto: true,
      transform: (_views) => {
        _views.forEach((view) => {
          view.columns = JSON.parse(view.columns || '[]')
          view.rows = JSON.parse(view.rows || '[]')
          view.filters = JSON.parse(view.filters || '{}')
        })
        return _views
      },
      onSuccess: () => setCurrentView(),
    })

    views[doctype] = reactive({
      ...toRefs(resource),
      currentView: null,
    })
  }

  function setCurrentView(view = null) {
    if (!views[doctype]?.data) return

    views[doctype].currentView =
      view || views[doctype].data.find((view) => view.is_default) || null
  }

  watch(
    () => doctype,
    () => setCurrentView(),
    { immediate: true },
  )

  return {
    resource: toRefs(views[doctype]),
    views: toRefs(views[doctype]).data,
    currentView: toRefs(views[doctype]).currentView,
  }
}
