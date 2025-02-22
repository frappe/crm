import { createRouter, createWebHistory } from 'vue-router'
import { userResource } from '@/stores/user'
import { sessionStore } from '@/stores/session'
import { viewsStore } from '@/stores/views'

// Define default view types for specific doctypes
const defaultViewTypes = {
  'CRM Lead': 'kanban',
  'CRM Deal': 'kanban',
  'CRM Task': 'kanban'
}

// Helper function to get default view type
function getDefaultViewType(routeName) {
  const doctypeMap = {
    'Leads': 'CRM Lead',
    'Deals': 'CRM Deal',
    'Tasks': 'CRM Task'
  }
  const doctype = doctypeMap[routeName]
  return defaultViewTypes[doctype] || 'list'
}

const routes = [
  {
    path: '/',
    name: 'Home',
  },
  {
    path: '/notifications',
    name: 'Notifications',
    component: () => import('@/pages/MobileNotification.vue'),
  },
  {
    alias: '/leads',
    path: '/leads/view/:viewType?',
    name: 'Leads',
    component: () => import('@/pages/Leads.vue'),
    meta: { scrollPos: { top: 0, left: 0 } },
  },
  {
    path: '/leads/:leadId',
    name: 'Lead',
    component: () => import(`@/pages/${handleMobileView('Lead')}.vue`),
    props: true,
  },
  {
    alias: '/deals',
    path: '/deals/view/:viewType?',
    name: 'Deals',
    component: () => import('@/pages/Deals.vue'),
    meta: { scrollPos: { top: 0, left: 0 } },
  },
  {
    path: '/deals/:dealId',
    name: 'Deal',
    component: () => import(`@/pages/${handleMobileView('Deal')}.vue`),
    props: true,
  },
  {
    alias: '/notes',
    path: '/notes/view/:viewType?',
    name: 'Notes',
    component: () => import('@/pages/Notes.vue'),
  },
  {
    alias: '/tasks',
    path: '/tasks/view/:viewType?',
    name: 'Tasks',
    component: () => import('@/pages/Tasks.vue'),
  },
  {
    alias: '/contacts',
    path: '/contacts/view/:viewType?',
    name: 'Contacts',
    component: () => import('@/pages/Contacts.vue'),
    meta: { scrollPos: { top: 0, left: 0 } },
  },
  {
    path: '/contacts/:contactId',
    name: 'Contact',
    component: () => import(`@/pages/${handleMobileView('Contact')}.vue`),
    props: true,
  },
  {
    alias: '/organizations',
    path: '/organizations/view/:viewType?',
    name: 'Organizations',
    component: () => import('@/pages/Organizations.vue'),
    meta: { scrollPos: { top: 0, left: 0 } },
  },
  {
    path: '/organizations/:organizationId',
    name: 'Organization',
    component: () => import(`@/pages/${handleMobileView('Organization')}.vue`),
    props: true,
  },
  {
    alias: '/call-logs',
    path: '/call-logs/view/:viewType?',
    name: 'Call Logs',
    component: () => import('@/pages/CallLogs.vue'),
    meta: { scrollPos: { top: 0, left: 0 } },
  },
  {
    alias: '/email-templates',
    path: '/email-templates/view/:viewType?',
    name: 'Email Templates',
    component: () => import('@/pages/EmailTemplates.vue'),
    meta: { scrollPos: { top: 0, left: 0 } },
  },
  {
    path: '/email-templates/:emailTemplateId',
    name: 'Email Template',
    component: () => import('@/pages/EmailTemplate.vue'),
    props: true,
  },
  {
    path: '/:invalidpath',
    name: 'Invalid Page',
    component: () => import('@/pages/InvalidPage.vue'),
  },
]

const handleMobileView = (componentName) => {
  return window.innerWidth < 768 ? `Mobile${componentName}` : componentName
}

const scrollBehavior = (to, from, savedPosition) => {
  if (to.name === from.name) {
    to.meta?.scrollPos && (to.meta.scrollPos.top = 0)
    return { left: 0, top: 0 }
  }
  const scrollpos = to.meta?.scrollPos || { left: 0, top: 0 }

  if (scrollpos.top > 0) {
    setTimeout(() => {
      let el = document.querySelector('#list-rows')
      el.scrollTo({
        top: scrollpos.top,
        left: scrollpos.left,
        behavior: 'smooth',
      })
    }, 300)
  }
}

let router = createRouter({
  history: createWebHistory('/crm'),
  routes,
  scrollBehavior,
})

router.beforeEach(async (to, from, next) => {
  const { isLoggedIn } = sessionStore()

  isLoggedIn && (await userResource.promise)

  if (from.meta?.scrollPos) {
    from.meta.scrollPos.top = document.querySelector('#list-rows')?.scrollTop
  }

  // Helper function to check if we should apply default view type
  const shouldApplyDefaultView = (to) => {
    // Check if this is a route that should have default kanban
    if (!['Leads', 'Deals', 'Tasks'].includes(to.name)) return false
    
    // Don't apply if there's an explicit view being loaded
    if (to.query.view) return false

    // Check if the URL ends with /view (empty viewType)
    const isEmptyViewType = to.params.viewType === ''
    
    // Check if this is a direct navigation to the base route
    const isBaseRoute = !to.params.viewType

    // Apply default view type if:
    // 1. URL ends with /view (empty viewType), or
    // 2. No viewType in URL (base route)
    return isEmptyViewType || isBaseRoute
  }

  if (to.name === 'Home' && isLoggedIn) {
    const { views, getDefaultView } = viewsStore()
    await views.promise

    let defaultView = getDefaultView()
    if (!defaultView) {
      next({ name: 'Leads', params: { viewType: getDefaultViewType('Leads') } })
      return
    }

    let { route_name, type, name, is_standard } = defaultView
    route_name = route_name || 'Leads'

    // If there's a saved view, respect its type
    if (name) {
      next({ name: route_name, params: { viewType: type || 'list' }, query: { view: name } })
    } else {
      // For standard views without explicit type, use our default
      next({ name: route_name, params: { viewType: type || getDefaultViewType(route_name) } })
    }
  } else if (!isLoggedIn) {
    window.location.href = '/login?redirect-to=/crm'
  } else if (to.matched.length === 0) {
    next({ name: 'Invalid Page' })
  } else if (['Deal', 'Lead'].includes(to.name) && !to.hash) {
    let storageKey = to.name === 'Deal' ? 'lastDealTab' : 'lastLeadTab'
    const activeTab = localStorage.getItem(storageKey) || 'activity'
    const hash = '#' + activeTab
    next({ ...to, hash })
  } else if (shouldApplyDefaultView(to)) {
    // Apply default view type
    next({ 
      ...to, 
      params: { 
        ...to.params, 
        viewType: getDefaultViewType(to.name)
      },
      replace: true // Replace the current history entry instead of adding a new one
    })
  } else {
    next()
  }
})

export default router
