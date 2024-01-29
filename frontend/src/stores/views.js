import { defineStore } from 'pinia'
import { sessionStore } from '@/stores/session'
import { createResource } from 'frappe-ui'
import { reactive, ref } from 'vue'

export const viewsStore = defineStore('crm-views', (doctype) => {
  let viewsByName = reactive({})
  let pinnedViews = ref([])
  let publicViews = ref([])
  let defaultView = ref(null)

  const { user } = sessionStore()

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
        if (view.pinned) {
          pinnedViews.value?.push(view)
        }
        if (view.public) {
          publicViews.value?.push(view)
        }

        if (
          (!view.public && view.default) ||
          (view.public &&
            view.default &&
            JSON.parse(view.user_list).includes(user))
        ) {
          defaultView.value = view
        }
      }
      return views
    },
  })

  function getView(view) {
    if (!view) return null
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

  function getDefaultView() {
    return defaultView.value
  }

  async function reload() {
    await views.reload()
  }

  return {
    views,
    getPinnedViews,
    getPublicViews,
    getDefaultView,
    reload,
    getView,
  }
})
