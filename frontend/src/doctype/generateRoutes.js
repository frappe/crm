import { createResource, FeatherIcon } from 'frappe-ui'
import { ref, h } from 'vue'

export const sidebarLayouts = ref([])

const sidebarLayoutResource = createResource({
  url: 'crm.fcrm.doctype.crm_ui_customization.crm_ui_customization.get_sidebar_layout',
  cache: 'App Sidebar',
  onSuccess: (data) => {
    if (data) {
      sidebarLayouts.value = data.map((item) => {
        return {
          ...item,
          icon: () => h(FeatherIcon, { name: item.icon || 'list' }),
        }
      })
    }
  },
})

export function fetchSidebarLayouts() {
  if (sidebarLayouts.value.length === 0) {
    return sidebarLayoutResource.fetch()
  }
}

export default async function generateRoutes() {
  let routes = []
  await fetchSidebarLayouts()
  const layouts = sidebarLayouts.value

  if (!layouts) {
    return routes
  }

  for (const object of layouts) {
    if (object.type == 'dynamic') {
      let routeName = `${object.doctype} List`
      object.routeName = routeName
      const _route = {
        name: routeName,
        path: object.route,
        component: () => import('@/pages/DynamicList.vue'),
        props: (route) => {
          return { ...object, ...route.params }
        },
      }
      routes.push(_route)
    }
  }

  return routes
}
