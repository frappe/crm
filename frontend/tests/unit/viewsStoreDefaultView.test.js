import { describe, it, expect, vi, beforeEach } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'

let serverViews = []

vi.mock('frappe-ui', () => ({
  createResource(options) {
    const resource = { data: [], promise: Promise.resolve() }
    resource.reload = async () => {
      resource.data = options.transform(serverViews)
    }
    resource.reload()
    return resource
  },
}))

function defaultView(route_name, name) {
  return { name, route_name, type: 'list', is_default: 1 }
}

async function storeWithViews(views) {
  serverViews = views
  const { viewsStore } = await import('@/stores/views')
  return viewsStore()
}

describe('viewsStore.getDefaultView', () => {
  beforeEach(() => {
    vi.resetModules()
    setActivePinia(createPinia())
  })

  it('returns the default for the requested route', async () => {
    const store = await storeWithViews([
      defaultView('Deals', 'My Deals'),
      defaultView('Leads', 'My Leads'),
    ])

    expect(store.getDefaultView('Deals').name).toBe('My Deals')
    expect(store.getDefaultView('Contacts')).toBeNull()
  })

  it('picks the home default by fixed route priority, not response order', async () => {
    const store = await storeWithViews([
      defaultView('Tasks', 'My Tasks'),
      defaultView('Deals', 'My Deals'),
      defaultView('Leads', 'My Leads'),
    ])

    expect(store.getDefaultView().name).toBe('My Leads')
  })

  it('falls back to sorted custom routes when no known route has a default', async () => {
    const store = await storeWithViews([
      defaultView('Zeta', 'Zeta View'),
      defaultView('Alpha', 'Alpha View'),
    ])

    expect(store.getDefaultView().name).toBe('Alpha View')
  })

  it('returns null when no default exists', async () => {
    const store = await storeWithViews([
      { name: 'Plain', route_name: 'Leads', type: 'list', is_default: 0 },
    ])

    expect(store.getDefaultView()).toBeNull()
  })
})
