import { defineStore } from 'pinia'
import { usersStore } from '@/stores/users'
import { createListResource } from 'frappe-ui'
import { reactive, ref } from 'vue'

export const viewsStore = defineStore('crm-views', () => {

  const { getUser } = usersStore()

  let viewsByName = reactive({})
  let pinnedViews = ref([])

  const views = createListResource({
    doctype: 'CRM View Settings',
    fields: ['*'],
    filters: { user: getUser().email },
    cache: 'crm-views',
    initialData: [],
    auto: true,
    transform(views) {
      pinnedViews.value = []
      for (let view of views) {
        viewsByName[view.name] = view
        if (view.pinned) {
          pinnedViews.value?.push(view)
        }
      }
      return views
    },
  })

  function getView(view) {
    if (!view) return null
    if (!viewsByName[view]) {
      views.reload()
    }
    return viewsByName[view]
  }

  function getPinnedViews() {
    if (!pinnedViews.value?.length) return []
    return pinnedViews.value
  }

  async function reload(wait = false) {
    await views.reload()
  }

  return {
    views,
    getPinnedViews,
    reload,
    getView,
  }
})
