import { defineStore } from 'pinia'
import { createResource } from 'frappe-ui'
import { sessionStore } from './session'
import { computed, reactive } from 'vue'

export const usersStore = defineStore('crm-users', () => {
  const session = sessionStore()

  let usersByName = reactive({})

  // Fast initial fetch — returns only the ~few CRM users so the UI is
  // interactive immediately. Non-CRM user profile data is filled in
  // afterwards by the background `usersFull` fetch (and by `get_user_info`
  // for the race window before that lands).
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
    onSuccess() {
      scheduleBackgroundFetch()
    },
  })

  // Background full-list fetch fired on browser idle. Only System Manager
  // sessions receive a larger payload here; for others the server returns
  // the same crm-users-only list. Populates usersByName so existing
  // getUser(email) call sites keep working for non-CRM emails (comment
  // authors, doc owners, email recipient typeahead, etc.).
  const usersFull = createResource({
    url: 'crm.api.session.get_users',
    params: { include_all: 1 },
    cache: 'crm-users-full',
    auto: false,
    transform([allUsers]) {
      for (let user of allUsers) {
        // upgrade partial get_user_info so always full record is used
        const existing = usersByName[user.name]
        if (existing) {
          Object.assign(existing, user)
        } else {
          usersByName[user.name] = user
        }
      }
      return { allUsers }
    },
  })

  let backgroundFetchScheduled = false
  function scheduleBackgroundFetch() {
    if (backgroundFetchScheduled) return
    backgroundFetchScheduled = true
    const fire = () => usersFull.fetch()
    if (typeof requestIdleCallback === 'function') {
      requestIdleCallback(fire, { timeout: 5000 })
    } else {
      setTimeout(fire, 2000)
    }
  }

  // Coalesced on-demand resolver. Used when getUser(email) is called for
  // an email that the fast fetch did not cover and the background full
  // fetch has not yet landed.
  const pendingResolves = new Set()
  let flushScheduled = false

  function queueResolve(email) {
    pendingResolves.add(email)
    if (flushScheduled) return
    flushScheduled = true
    queueMicrotask(flush)
  }

  async function flush() {
    flushScheduled = false
    if (!pendingResolves.size) return
    const batch = [...pendingResolves]
    pendingResolves.clear()
    try {
      const r = createResource({
        url: 'crm.api.session.get_user_info',
        params: { users: batch },
        auto: false,
      })
      const records = await r.fetch()
      for (const u of records || []) {
        usersByName[u.name] = { ...usersByName[u.name], ...u }
      }
    } catch (e) {
      // best-effort — the synthesized stub remains on failure
    }
  }

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
      // Try to upgrade the stub via a batched fetch unless the full list
      // has already arrived.
      if (!usersFull.data) {
        queueResolve(email)
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
    return getUser(email).is_telephony_agent
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
    usersFull,
    allUsers: computed(() => usersFull.data?.allUsers || users.data?.allUsers),
    crmUsers: computed(() => users.data?.crmUsers),
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
