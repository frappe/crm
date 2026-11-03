import { defineStore } from 'pinia'
import { createResource } from 'frappe-ui'
import router from '@/router'
import { getSessionUser } from '@/utils/session'
import { ref, computed } from 'vue'

export const sessionStore = defineStore('crm-session', () => {
  let user = ref(getSessionUser())
  const isLoggedIn = computed(() => !!user.value)

  const login = createResource({
    url: 'login',
    onError() {
      throw new Error(__('Invalid Email or Password'))
    },
    onSuccess() {
      user.value = getSessionUser()
      login.reset()
      router.replace({ path: '/' })
    },
  })

  const logout = createResource({
    url: 'logout',
    onSuccess() {
      user.value = null
      window.location.href = '/login?redirect-to=/crm'
    },
  })

  return {
    user,
    isLoggedIn,
    login,
    logout,
  }
})
