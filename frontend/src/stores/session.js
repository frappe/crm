import { defineStore } from 'pinia'
import { createResource } from 'frappe-ui'
import { usersStore } from './users'
import router from '@/router'
import { ref, computed } from 'vue'

export const sessionStore = defineStore('crm-session', () => {
  const { users } = usersStore()

  function sessionUser() {
    let cookies = new URLSearchParams(document.cookie.split('; ').join('&'))
    let _sessionUser = cookies.get('user_id')
    if (_sessionUser === 'Guest') {
      _sessionUser = null
    }
    return _sessionUser
  }

  let user = ref(sessionUser())
  const isLoggedIn = computed(() => !!user.value)

  const login = createResource({
    url: 'login',
    onError() {
      throw new Error('Invalid email or password')
    },
    onSuccess() {
      users.reload()
      user.value = sessionUser()
      login.reset()
      router.replace({ path: '/' })
    },
  })

  const logout = createResource({
    url: 'logout',
    onSuccess() {
      users.reset()
      user.value = null
      router.replace({ name: 'Login' })
    },
  })

  return {
    user,
    isLoggedIn,
    login,
    logout,
  }
})
