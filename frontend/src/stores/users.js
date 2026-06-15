import { defineStore } from 'pinia'
import { createResource } from 'frappe-ui'
import { sessionStore } from './session'
import { computed, reactive } from 'vue'

export const usersStore = defineStore('crm-users', () => {
  const session = sessionStore()

  let usersByName = reactive({})

  const users = createResource({
    url: 'crm.api.session.get_users',
    cache: 'crm-users',
    initialData: [],
    auto: true,
    transform([allUsers, crmUsers]) {
      for (let user of allUsers) {
        usersByName[user.name] = user
        if (user.name === 'Administrator') {
          usersByName[user.email] = user
        }
      }
      return { allUsers, crmUsers }
    },
    onError(error) {
      const isAuthError = ['AuthenticationError', 'PermissionError'].includes(
        error?.exc_type,
      )

      if (isAuthError) {
        window.location.href = '/login?redirect-to=/crm'
      }
    },
  })

  function getUser(email) {
    if (!email || email === 'sessionUser') {
      email = session.user
    }
    if (!usersByName[email]) {
      usersByName[email] = {
        name: email,
        email: email,
        full_name: email.split('@')[0],
        first_name: email.split('@')[0],
        last_name: '',
        user_image: null,
        role: null,
      }
    }
    return usersByName[email]
  }

  function isAdmin(email) {
    return getUser(email).role === 'System Manager'
  }

  function isManager(email) {
    return getUser(email).role === 'Sales Manager' || isAdmin(email)
  }

  function isWebsiteUser(email) {
    return getUser(email).user_type === 'Website User'
  }

  function isSalesUser(email) {
    return getUser(email).role === 'Sales User'
  }

  function isTelephonyAgent(email) {
    return getUser(email).is_telphony_agent
  }

  function getUserRole(email) {
    const user = getUser(email)
    if (user && user.role) {
      return user.role
    }
    return null
  }

  const isCrmUser = (user) => {
    user = user || session.user
    return users.data.crmUsers?.find((u) => u.name === user)
  }

  return {
    users,
    allUsers: computed(() => users.data.allUsers),
    crmUsers: computed(() => users.data.crmUsers),
    getUser,
    isAdmin,
    isManager,
    isSalesUser,
    isTelephonyAgent,
    getUserRole,
    isWebsiteUser,
    isCrmUser,
  }
})
