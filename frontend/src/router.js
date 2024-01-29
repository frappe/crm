import { createRouter, createWebHistory } from 'vue-router'
import { usersStore } from '@/stores/users'
import { sessionStore } from '@/stores/session'
import { viewsStore } from '@/stores/views'

const routes = [
  {
    path: '/',
    name: 'Home',
  },
  {
    path: '/leads',
    name: 'Leads',
    component: () => import('@/pages/Leads.vue'),
    meta: { scrollPos: { top: 0, left: 0 } },
  },
  {
    path: '/leads/:leadId',
    name: 'Lead',
    component: () => import('@/pages/Lead.vue'),
    props: true,
  },
  {
    path: '/deals',
    name: 'Deals',
    component: () => import('@/pages/Deals.vue'),
    meta: { scrollPos: { top: 0, left: 0 } },
  },
  {
    path: '/deals/:dealId',
    name: 'Deal',
    component: () => import('@/pages/Deal.vue'),
    props: true,
  },
  {
    path: '/notes',
    name: 'Notes',
    component: () => import('@/pages/Notes.vue'),
  },
  {
    path: '/contacts',
    name: 'Contacts',
    component: () => import('@/pages/Contacts.vue'),
    meta: { scrollPos: { top: 0, left: 0 } },
  },
  {
    path: '/contacts/:contactId',
    name: 'Contact',
    component: () => import('@/pages/Contact.vue'),
    props: true,
  },
  {
    path: '/organizations',
    name: 'Organizations',
    component: () => import('@/pages/Organizations.vue'),
    meta: { scrollPos: { top: 0, left: 0 } },
  },
  {
    path: '/organizations/:organizationId',
    name: 'Organization',
    component: () => import('@/pages/Organization.vue'),
    props: true,
  },
  {
    path: '/call-logs',
    name: 'Call Logs',
    component: () => import('@/pages/CallLogs.vue'),
    meta: { scrollPos: { top: 0, left: 0 } },
  },
  {
    path: '/call-logs/:callLogId',
    name: 'Call Log',
    component: () => import('@/pages/CallLog.vue'),
    props: true,
  },
  {
    path: '/email-templates',
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
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('@/pages/Dashboard.vue'),
  },
  {
    path: '/:invalidpath',
    name: 'Invalid Page',
    component: () => import('@/pages/InvalidPage.vue'),
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/pages/Login.vue'),
  },
]

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
  const { users } = usersStore()
  const { isLoggedIn } = sessionStore()
  const { views, getDefaultView } = viewsStore()

  await users.promise
  await views.promise

  if (from.meta?.scrollPos) {
    from.meta.scrollPos.top = document.querySelector('#list-rows')?.scrollTop
  }

  if (to.path === '/') {
    const defaultView = getDefaultView()
    if (defaultView?.route_name) {
      if (defaultView.is_view) {
        next({
          name: defaultView.route_name,
          query: { view: defaultView.name },
        })
      } else {
        next({ name: defaultView.route_name })
      }
    } else {
      next({ name: 'Leads' })
    }
  } else if (to.name === 'Login' && isLoggedIn) {
    next({ name: 'Leads' })
  } else if (to.name !== 'Login' && !isLoggedIn) {
    next({ name: 'Login' })
  } else if (to.matched.length === 0) {
    next({ name: 'Invalid Page' })
  } else {
    next()
  }
})

export default router
