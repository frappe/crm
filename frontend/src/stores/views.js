import { defineStore } from 'pinia'
import { createListResource } from 'frappe-ui'
import { reactive } from 'vue'

export const viewsStore = defineStore('crm-views', () => {
  let viewsByName = reactive({})

  const views = createListResource({
    doctype: 'CRM View Settings',
    fields: ['*'],
    cache: 'crm-views',
    initialData: [],
    auto: true,
    transform(views) {
      for (let view of views) {
        viewsByName[view.name] = view
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

  return {
    views,
    getView,
  }
})
