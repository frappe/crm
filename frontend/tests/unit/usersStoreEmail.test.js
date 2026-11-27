import { describe, it, expect, vi, beforeEach } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'

// A user whose ID is not their email.
const jane = {
  name: 'ab12cd34ef',
  email: 'jane@example.com',
  full_name: 'Jane Doe',
  role: 'Sales User',
}

const server = vi.hoisted(() => ({ responses: {}, resources: {} }))

vi.mock('frappe-ui', () => ({
  createResource(options) {
    const key = options.params?.include_all
      ? 'get_users_full'
      : options.url.split('.').pop()
    const resource = {
      data: options.initialData ?? null,
      async fetch() {
        const raw = server.responses[key]
        resource.data = options.transform ? options.transform(raw) : raw
        return resource.data
      },
    }
    server.resources[key] = resource
    return resource
  },
}))

vi.mock('@/stores/session', () => ({
  sessionStore: () => ({ user: 'Administrator' }),
}))

async function freshStore() {
  const { usersStore } = await import('@/stores/users')
  return usersStore()
}

describe('usersStore.getUser by email', () => {
  beforeEach(() => {
    vi.resetModules()
    setActivePinia(createPinia())
    server.responses = {}
    server.resources = {}
  })

  it('finds a user by email after the fast fetch', async () => {
    server.responses.get_users = [[jane], [jane]]
    const store = await freshStore()
    await server.resources.get_users.fetch()

    const user = store.getUser('jane@example.com')
    expect(user.name).toBe('ab12cd34ef')
    expect(user.full_name).toBe('Jane Doe')
    expect(store.getUser('ab12cd34ef')).toBe(user)
  })

  it('finds a user by email after the background full fetch', async () => {
    server.responses.get_users = [[], []]
    server.responses.get_users_full = [[jane]]
    const store = await freshStore()
    await server.resources.get_users.fetch()
    await server.resources.get_users_full.fetch()

    const user = store.getUser('jane@example.com')
    expect(user.name).toBe('ab12cd34ef')
    expect(user.full_name).toBe('Jane Doe')
  })

  it('finds a user by email after get_user_info resolves a stub by ID', async () => {
    server.responses.get_users = [[], []]
    server.responses.get_user_info = [jane]
    const store = await freshStore()
    await server.resources.get_users.fetch()

    // unknown ID -> stub, then batched get_user_info upgrades it
    expect(store.getUser('ab12cd34ef').full_name).toBe('ab12cd34ef')
    await vi.waitFor(() =>
      expect(store.getUser('ab12cd34ef').full_name).toBe('Jane Doe'),
    )

    const user = store.getUser('jane@example.com')
    expect(user.name).toBe('ab12cd34ef')
    expect(user.full_name).toBe('Jane Doe')
  })

  it('keeps finding users whose ID is their email', async () => {
    const legacy = { name: 'bob@example.com', email: 'bob@example.com' }
    server.responses.get_users = [[legacy], [legacy]]
    const store = await freshStore()
    await server.resources.get_users.fetch()

    expect(store.getUser('bob@example.com').name).toBe('bob@example.com')
  })
})
