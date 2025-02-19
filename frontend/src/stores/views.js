import { defineStore } from 'pinia'
import { createResource } from 'frappe-ui'
import { reactive, ref } from 'vue'

export const viewsStore = defineStore('crm-views', (doctype) => {
  let viewsByName = reactive({})
  let pinnedViews = ref([])
  let publicViews = ref([])
  let standardViews = ref({})

  // Default view
  const defaultView = createResource({
    url: 'crm.api.views.get_default_view',
    cache: 'crm-default-view',
    auto: true,
  })

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
      for (let view of views) {
        viewsByName[view.name] = view
        view.type = view.type || 'list'
        if (view.pinned) {
          pinnedViews.value?.push(view)
        }
        if (view.public) {
          publicViews.value?.push(view)
        }
        if (view.is_default && view.dt) {
          standardViews.value[view.dt + ' ' + view.type] = view
        }
      }
      return views
    },
  })

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
    standardViews,
    getPinnedViews,
    getPublicViews,
    reload,
    getView,
  }
})
