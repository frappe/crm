import { getLandingPage, landingRoute, landingViews } from '@/utils/landingPage'

const hasRoute = (name) => ['Leads', 'Deals', 'Dashboard'].includes(name)

const views = [
  {
    name: 'v-own',
    user: 'me@example.com',
    route_name: 'Deals',
    type: 'kanban',
  },
  { name: 'v-public', user: '', public: 1, route_name: 'Leads', type: 'list' },
  { name: 'v-pinned', user: '', pinned: 1, route_name: 'Leads', type: 'list' },
  { name: 'v-other', user: 'other@example.com', route_name: 'Leads' },
  { name: 'v-standard', user: 'me@example.com', is_standard: 1 },
]

describe('getLandingPage', () => {
  it('defaults to Home', () => {
    window.sysdefaults = {}
    expect(getLandingPage()).toBe('Home')
    window.sysdefaults = { crm_landing_page: 'Deals' }
    expect(getLandingPage()).toBe('Deals')
  })
})

describe('landingRoute', () => {
  it('stays on Home for Home', () => {
    expect(landingRoute('Home', views, hasRoute)).toBeNull()
  })

  it('opens a saved view with its type', () => {
    expect(landingRoute('v-own', views, hasRoute)).toEqual({
      name: 'Deals',
      params: { viewType: 'kanban' },
      query: { view: 'v-own' },
    })
  })

  it('opens a page by route name', () => {
    expect(landingRoute('Dashboard', views, hasRoute)).toEqual({
      name: 'Dashboard',
    })
  })

  it('falls back to Home for a deleted view', () => {
    expect(landingRoute('v-deleted', views, hasRoute)).toBeNull()
  })
})

describe('landingViews', () => {
  it("offers the user's own, public and pinned views", () => {
    expect(landingViews(views, 'me@example.com').map((v) => v.name)).toEqual([
      'v-own',
      'v-public',
      'v-pinned',
    ])
  })
})
