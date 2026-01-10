import { createResource } from 'frappe-ui'
import { reactive, watch, toRefs } from 'vue'

const view = reactive({})
const views = reactive({})

function normalizeView(view) {
  view.columns = JSON.parse(view.columns || '[]')
  view.rows = JSON.parse(view.rows || '[]')
  view.filters = JSON.parse(view.filters || '{}')
  view.type = view.type || 'list'
  return view
}

export function useView(doctype, viewName = null) {
  if (!view[doctype]?.[viewName]) {
    const resource = createResource({
      url: 'crm.api.views.get_current_view',
      params: { doctype: doctype, view_name: viewName },
      cache: ['CRM Views', doctype, viewName],
      auto: true,
      transform: (view) => normalizeView(view),
      onSuccess: () => setCurrentView(),
    })

    if (!view[doctype]) {
      view[doctype] = {}
    }

    view[doctype][viewName] = reactive({
      ...toRefs(resource),
      currentView: null,
    })
  }

  function setCurrentView(v = null) {
    if (!view[doctype]?.[viewName]?.data) return

    view[doctype][viewName].currentView =
      v || view[doctype][viewName].data || null
  }

  watch(
    () => doctype,
    () => setCurrentView(),
    { immediate: true },
  )

  const viewRefs = toRefs(view[doctype][viewName])
  return {
    resource: viewRefs,
    view: viewRefs.data,
    currentView: viewRefs.currentView,
  }
}

export function useViews() {
  if (!views?.resource) {
    const resource = createResource({
      url: 'crm.api.views.get_views',
      cache: 'All Views',
      auto: true,
      transform: (_views) => parseViews(_views),
    })

    views.resource = reactive(resource)
    views.publicViews = reactive([])
    views.pinnedViews = reactive([])
  }

  function parseViews(_views) {
    const pinned = []
    const publics = []

    const parsed = _views.map((view) => {
      const normalized = normalizeView(view)
      if (normalized.pinned) pinned.push(normalized)
      if (normalized.public) publics.push(normalized)
      return normalized
    })

    views.pinnedViews.splice(0, views.pinnedViews.length, ...pinned)
    views.publicViews.splice(0, views.publicViews.length, ...publics)

    return parsed
  }

  const viewRefs = toRefs(views)
  return {
    resource: viewRefs.resource,
    publicViews: viewRefs.publicViews,
    pinnedViews: viewRefs.pinnedViews,
  }
}
