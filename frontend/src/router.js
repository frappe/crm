import { createRouter, createWebHistory } from 'vue-router'
import { usersStore } from '@/stores/users'
import { sessionStore } from '@/stores/session'

const routes = [
  {
    path: '/',
    redirect: '/leads',
  },
  {
    path: '/leads',
    name: 'Leads',
    component: () => import('@/pages/Leads.vue'),
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
  },
  {
    path: '/deals/:dealId',
    name: 'Deal',
    component: () => import('@/pages/Deal.vue'),
    props: true,
  },
  {
    path: '/inbox',
    name: 'Inbox',
    component: () => import('@/pages/Inbox.vue'),
  },
  {
    path: '/contacts',
    name: 'Contacts',
    component: () => import('@/pages/Contacts.vue'),
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

let router = createRouter({
  history: createWebHistory('/crm'),
  routes,
})

router.beforeEach(async (to, from, next) => {
  const { users } = usersStore()
  const { isLoggedIn } = sessionStore()

  await users.promise

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
