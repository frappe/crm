import { it, expect, vi } from 'vitest'
import { createApp } from 'vue'

const jane = {
  name: 'ab12cd34ef',
  email: 'jane@example.com',
  full_name: 'Jane Doe',
  role: 'Sales User',
}

vi.mock('frappe-ui', () => {
  const stub = { render: () => null }
  return {
    createResource: () => ({ reload: () => {}, submit: () => {} }),
    createListResource: () => ({ data: [], reload: () => {} }),
    call: () => Promise.resolve(),
    toast: { success: () => {}, error: () => {} },
    Dropdown: stub,
    Avatar: stub,
    TextInput: stub,
    Tooltip: stub,
    Select: stub,
    FormControl: stub,
    Button: stub,
    Dialog: stub,
    Badge: stub,
  }
})

vi.mock('@/stores/users', () => ({
  usersStore: () => ({
    users: { data: { crmUsers: [jane], allUsers: [jane] } },
    allUsers: { value: [jane] },
    isAdmin: () => true,
    isManager: () => true,
  }),
}))

vi.mock('@/composables/onboarding', () => ({
  useCrmOnboarding: () => ({ completeStep: () => {} }),
}))

vi.mock('@framework/ui/telemetry', () => ({
  useTelemetry: () => ({ capture: () => {} }),
}))

import Users from '@/components/Settings/Users.vue'
import InviteUserPage from '@/components/Settings/InviteUserPage.vue'

function mount(component) {
  const app = createApp(component)
  app.config.globalProperties.__ = (text) => text
  app.mount(document.createElement('div'))
  return { app, state: app._instance.setupState }
}

it('Users settings search finds a user by email', () => {
  const { app, state } = mount(Users)
  try {
    state.search = 'jane@'
    expect(state.usersList.map((u) => u.name)).toEqual(['ab12cd34ef'])
  } finally {
    app.unmount()
  }
})

it('Invite page flags an email that already belongs to a CRM user', () => {
  const { app, state } = mount(InviteUserPage)
  try {
    state.invitees = ['jane@example.com']
    expect(state.userExistMessage).toBe(
      'User with email jane@example.com already exists',
    )
  } finally {
    app.unmount()
  }
})
