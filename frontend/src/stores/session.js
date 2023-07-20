import { defineStore } from 'pinia'
import { createResource } from 'frappe-ui'
import router from '@/router'
import { computed } from 'vue'

export const sessionStore = defineStore('crm-session', () => {
  const sessionUser = createResource({
    url: 'crm.api.session.get_user_info',
  })

  const user = computed(() => sessionUser.data || null)
  const isLoggedIn = computed(() => !!user.value)

  const login = createResource({
    url: 'login',
    onError() {
      throw new Error('Invalid email or password')
    },
    onSuccess() {
      router.replace({ path: '/' })
    },
  })

  const logout = createResource({
    url: 'logout',
    onSuccess() {
      router.replace({ name: 'Login' })
    },
  })

  async function init() {
    try {
      await sessionUser.fetch()
    } catch {
      sessionUser.data = null
    }
  }

  return {
    user,
    isLoggedIn,
    login,
    logout,
    init,
  }
})
