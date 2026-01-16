import { toKebabCase } from '@/utils'
import { useCall } from 'frappe-ui'
import { ref } from 'vue'

export const sidebarLayouts = ref([])
export const doctypeRoutes = ref([])

useCall({
  url: '/api/v2/method/crm.fcrm.doctype.crm_ui_customization.crm_ui_customization.get_sidebar_layout',
  cacheKey: 'App Sidebar Layouts',
  onSuccess: (data) => {
    sidebarLayouts.value =
      data?.map((item) => ({ ...item, icon: item.icon || 'list' })) || []
  },
})

const doctypesList = useCall({
  url: '/api/v2/method/crm.api.views.get_doctype_list',
  cacheKey: 'DocType List',
  onSuccess: (data) => (doctypeRoutes.value = data || []),
})

export default async function generateRoutes() {
  let routes = []

  await doctypesList.promise

  if (!doctypeRoutes.value?.length) return routes

  for (const r of doctypeRoutes.value) {
    let routeName = `${r.name} List`
    r.routeName = routeName
    const _route = {
      name: routeName,
      path: r.route || `/${toKebabCase(r.name)}`,
      component: () => import('@/pages/List.vue'),
      children: [
        {
          name: `${routeName} View`,
          path: 'view/:viewName?',
          component: () => import('@/pages/List.vue'),
          props: (route) => ({
            doctype: r.name,
            routeName: r.routeName,
            ...route.params,
          }),
        },
      ],
      props: (route) => ({
        doctype: r.name,
        routeName: r.routeName,
        ...route.params,
      }),
    }
    routes.push(_route)
  }

  return routes
}
