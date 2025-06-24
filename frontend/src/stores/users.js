import { defineStore } from 'pinia'
import { createResource } from 'frappe-ui'
import { sessionStore } from './session'
import { reactive } from 'vue'
import { useRouter } from 'vue-router'

export const usersStore = defineStore('crm-users', () => {
  const session = sessionStore()

  let usersByName = reactive({})
  const router = useRouter()

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
      if (error && error.exc_type === 'AuthenticationError') {
        router.push('/login')
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
    return getUser(email).role === 'System Manager' || getUser(email).is_admin
  }

  function isManager(email) {
    return getUser(email).is_manager
  }

  function isAgent(email) {
    return getUser(email).is_agent
  }

  function getUserRole(email) {
    const user = getUser(email)
    if (user && user.role) {
      return user.role
    }
    return null
  }

  return {
    users,
    getUser,
    isAdmin,
    isManager,
    isAgent,
    getUserRole,
  }
})
