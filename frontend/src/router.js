import { createRouter, createWebHistory } from 'vue-router'
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
    path: '/deals',
    name: 'Deals',
    component: () => import('@/pages/Deals.vue'),
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
  const session = sessionStore()

  // Initialize session
  await session.init()

  if (to.name === 'Login' && session.isLoggedIn) {
    next({ name: 'Leads' })
  } else if (to.name !== 'Login' && !session.isLoggedIn) {
    next({ name: 'Login' })
  } else if (to.matched.length === 0) {
    next({ name: 'Invalid Page' })
  } else {
    next()
  }
})

export default router
