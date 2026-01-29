import { useCall } from 'frappe-ui'
import { reactive, toRefs } from 'vue'

const view = reactive({})
const views = reactive({})

function normalizeView(v) {
  if (!v) return null

  v.columns =
    typeof v.columns == 'string' ? JSON.parse(v.columns || '[]') : v.columns
  v.rows = typeof v.rows == 'string' ? JSON.parse(v.rows || '[]') : v.rows
  v.filters =
    typeof v.filters == 'string' ? JSON.parse(v.filters || '{}') : v.filters
  v.type = v.type || 'list'
  return v
}

export function useView(doctype, viewName = null) {
  if (!view[doctype]?.[viewName]) {
    const resource = useCall({
      url: '/api/v2/method/crm.api.views.get_current_view',
      method: 'GET',
      params: { doctype, view_name: viewName },
      cacheKey: ['Current View', doctype, viewName],
      refetch: true,
      transform: (v) => normalizeView(v),
      onSuccess: (v) => setCurrentView(v),
    })

    if (!view[doctype]) {
      view[doctype] = {}
    }

    view[doctype][viewName] = reactive({
      ...toRefs(resource),
      currentView: null,
    })
  }

  function setCurrentView(viewData) {
    view[doctype][viewName].currentView = viewData || null
  }

  function reload(reloadList = null) {
    if (view[doctype][viewName].isFetching) return
    view[doctype][viewName].reload().then(() => reloadList?.())
  }

  const viewRefs = toRefs(view[doctype][viewName])
  return {
    resource: viewRefs,
    currentView: viewRefs.currentView,
    reloadCurrentView: reload,
  }
}

export function useViews() {
  if (!views?.resource) {
    const resource = useCall({
      url: '/api/v2/method/crm.api.views.get_views',
      method: 'GET',
      cacheKey: 'All Views',
      transform: (_views) => parseViews(_views),
    })

    views.resource = reactive(resource)
    views.publicViews = reactive([])
    views.pinnedViews = reactive([])
    views.allViews = reactive([])
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
    views.allViews = parsed

    return parsed
  }

  const viewRefs = toRefs(views)
  return {
    resource: viewRefs.resource,
    allViews: viewRefs.allViews,
    publicViews: viewRefs.publicViews,
    pinnedViews: viewRefs.pinnedViews,
    reloadViews: views.resource.reload,
  }
}
