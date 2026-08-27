import { defineStore } from 'pinia'
import { createResource } from 'frappe-ui'
import { computed, reactive, ref } from 'vue'

export const viewsStore = defineStore('crm-views', (doctype) => {
  if (typeof doctype !== 'string') {
    doctype = null
  }

  let viewsByName = reactive({})
  let pinnedViews = ref([])
  let publicViews = ref([])
  let standardViews = ref({})
  // Keyed by route_name (e.g. 'Leads', 'Deals') so each doctype keeps its own default
  const defaultViews = reactive({})

  // Views
  const views = createResource({
    url: 'crm.api.views.get_views',
    params: { doctype: doctype || '' },
    cache: 'crm-views',
    initialData: [],
    auto: true,
    transform(views) {
      pinnedViews.value = []
      publicViews.value = []
      // Reset per-doctype defaults before repopulating
      Object.keys(defaultViews).forEach((k) => delete defaultViews[k])
      for (let view of views) {
        viewsByName[view.name] = view
        view.type = view.type || 'list'
        if (view.pinned) {
          pinnedViews.value?.push(view)
        }
        if (view.public) {
          publicViews.value?.push(view)
        }
        if (view.is_standard && view.dt) {
          standardViews.value[view.dt + ' ' + view.type] = view
        }
        if (view.is_default && view.route_name) {
          defaultViews[view.route_name] = view
        }
      }
      return views
    },
  })

  function getDefaultView(routeName = null) {
    if (routeName) return defaultViews[routeName] || null
    // Fallback for Home redirect: return first registered default
    const keys = Object.keys(defaultViews)
    return keys.length ? defaultViews[keys[0]] : null
  }

  // Backwards-compatible alias for consumers still reading `defaultView`
  // directly off the store (previously a single ref, now derived from the
  // first entry in `defaultViews`). Prefer `getDefaultView(routeName)`.
  const defaultView = computed(() => getDefaultView())

  function getView(view, type, doctype = null) {
    type = type || 'list'
    if (!view && doctype) {
      return standardViews.value[doctype + ' ' + type] || null
    }
    return viewsByName[view]
  }

  function getPinnedViews() {
    if (!pinnedViews.value?.length) return []
    return pinnedViews.value
  }

  function getPublicViews() {
    if (!publicViews.value?.length) return []
    return publicViews.value
  }

  async function reload() {
    await views.reload()
  }

  return {
    views,
    defaultView,
    defaultViews,
    standardViews,
    getDefaultView,
    getPinnedViews,
    getPublicViews,
    reload,
    getView,
  }
})
