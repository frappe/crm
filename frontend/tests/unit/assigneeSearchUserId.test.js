import { describe, it, expect, vi } from 'vitest'
import { createApp, ref } from 'vue'

const jane = {
  name: 'ab12cd34ef',
  email: 'jane@example.com',
  full_name: 'Jane Doe',
  user_image: null,
}

vi.mock('frappe-ui', () => ({
  Popover: { render: () => null },
  Button: { render: () => null },
}))

vi.mock('@/stores/users', () => ({
  usersStore: () => ({ users: { data: { crmUsers: [jane] } } }),
}))

vi.mock('@/stores/global', () => ({
  globalStore: () => ({ $dialog: () => {} }),
}))

import AssigneeSearch from '@/components/Settings/AssignmentRules/AssigneeSearch.vue'

function mountSearch(users = []) {
  const assignmentRuleData = ref({ users })
  const app = createApp(AssigneeSearch)
  app.config.globalProperties.__ = (text) => text
  app.provide('assignmentRuleData', assignmentRuleData)
  app.mount(document.createElement('div'))
  return { app, state: app._instance.setupState, assignmentRuleData }
}

describe('AssigneeSearch with user IDs', () => {
  it('stores the user ID in the rule row', () => {
    const { app, state, assignmentRuleData } = mountSearch()
    try {
      state.addAssignee(jane)
      expect(assignmentRuleData.value.users).toHaveLength(1)
      expect(assignmentRuleData.value.users[0].user).toBe('ab12cd34ef')
      expect(assignmentRuleData.value.users[0].email).toBe('jane@example.com')
    } finally {
      app.unmount()
    }
  })

  it('does not add the same user twice', () => {
    const { app, state, assignmentRuleData } = mountSearch([
      { user: 'ab12cd34ef', email: 'jane@example.com' },
    ])
    try {
      state.addAssignee(jane)
      expect(assignmentRuleData.value.users).toHaveLength(1)
    } finally {
      app.unmount()
    }
  })

  it('hides users already in the rule from the list', () => {
    const { app, state } = mountSearch([{ user: 'ab12cd34ef' }])
    try {
      expect(state.usersList).toEqual([])
    } finally {
      app.unmount()
    }
  })

  it('finds a user by email in the search', () => {
    const { app, state } = mountSearch()
    try {
      state.query = 'jane@'
      expect(state.usersList.map((u) => u.name)).toEqual(['ab12cd34ef'])
    } finally {
      app.unmount()
    }
  })
})
