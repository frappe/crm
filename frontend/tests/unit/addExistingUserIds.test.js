import { it, expect, vi } from 'vitest'
import { computed, createApp, nextTick } from 'vue'

const jane = {
  name: 'ab12cd34ef',
  email: 'jane@example.com',
  full_name: 'Jane Doe',
}

const resources = vi.hoisted(() => ({}))

vi.mock('frappe-ui', () => ({
  createResource(options) {
    resources[options.url] = options
    return { loading: false, submit: () => {} }
  },
  toast: { success: () => {}, error: () => {} },
  Dialog: { render: () => null },
  FormControl: { render: () => null },
  Button: { render: () => null },
}))

vi.mock('@/stores/users', () => ({
  usersStore: () => ({
    users: { data: { crmUsers: [], allUsers: [jane] } },
    allUsers: computed(() => [jane]),
    isAdmin: () => true,
  }),
}))

import AddExistingUserModal from '@/components/Modals/AddExistingUserModal.vue'

it('sends user IDs, not emails, to add_existing_users', async () => {
  const app = createApp(AddExistingUserModal)
  app.config.globalProperties.__ = (text) => text
  app.mount(document.createElement('div'))
  try {
    app._instance.setupState.newUsers = ['jane@example.com']
    await nextTick()

    const params = resources['crm.api.user.add_existing_users'].makeParams()
    expect(JSON.parse(params.users)).toEqual(['ab12cd34ef'])
  } finally {
    app.unmount()
  }
})
