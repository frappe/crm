import { createRouter, createWebHistory } from 'vue-router'
import { userResource } from '@/stores/user'
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
    alias: '/opportunities',
    path: '/opportunities/view/:viewType?',
    name: 'Opportunities',
    component: () => import('@/pages/Opportunities.vue'),
    meta: { scrollPos: { top: 0, left: 0 } },
  },
  {
    path: '/opportunities/:opportunityId',
    name: 'Opportunity',
    component: () => import(`@/pages/${handleMobileView('Opportunity')}.vue`),
    props: true,
  },
  {
    alias: '/todos',
    path: '/todos/view/:viewType?',
    name: 'ToDos',
    component: () => import('@/pages/ToDos.vue'),
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
    alias: '/customers',
    path: '/customers/view/:viewType?',
    name: 'Customers',
    component: () => import('@/pages/Customers.vue'),
    meta: { scrollPos: { top: 0, left: 0 } },
  },
  {
    path: '/customers/:customerId',
    name: 'Customer',
    component: () => import(`@/pages/${handleMobileView('Customer')}.vue`),
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
    alias: '/prospects',
    path: '/prospects/view/:viewType?',
    name: 'Prospects',
    component: () => import('@/pages/Prospects.vue'),
    meta: { scrollPos: { top: 0, left: 0 } },
  },
  {
    path: '/prospects/:prospectId',
    name: 'Prospect',
    component: () => import(`@/pages/Prospect.vue`),
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
  history: createWebHistory('/next-crm'),
  routes,
  scrollBehavior,
})

router.beforeEach(async (to, from, next) => {
  const { isLoggedIn } = sessionStore()

  isLoggedIn && (await userResource.promise)

  if (from.meta?.scrollPos) {
    from.meta.scrollPos.top = document.querySelector('#list-rows')?.scrollTop
  }

  if (to.name === 'Home' && isLoggedIn) {
    next({ name: 'Leads' })
  } else if (!isLoggedIn) {
    window.location.href = '/login?redirect-to=/next-crm'
  } else if (to.matched.length === 0) {
    next({ name: 'Invalid Page' })
  } else if (['Opportunity', 'Lead'].includes(to.name) && !to.hash) {
    let storageKey = to.name === 'Opportunity' ? 'lastOpportunityTab' : 'lastLeadTab'
    const activeTab = localStorage.getItem(storageKey) || 'activity'
    const hash = '#' + activeTab
    next({ ...to, hash })
  } else {
    next()
  }
})

export default router
