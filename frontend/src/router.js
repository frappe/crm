import { createRouter, createWebHistory } from 'vue-router'
import { usersStore } from '@/stores/users'
import { sessionStore } from '@/stores/session'

const routes = [
  {
    path: '/',
    redirect: { name: 'Leads' },
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
    path: '/notes',
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
  const { users } = usersStore()
  const { isLoggedIn } = sessionStore()

  isLoggedIn && (await users.promise)

  if (from.meta?.scrollPos) {
    from.meta.scrollPos.top = document.querySelector('#list-rows')?.scrollTop
  }

  if (to.name === 'Login' && isLoggedIn) {
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
