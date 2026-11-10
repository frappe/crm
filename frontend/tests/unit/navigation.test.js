import {
  getNavigationItems,
  getNavigationSections,
  navigationItems,
  navigationSections,
} from '@/utils/navigation'

describe('navigationItems', () => {
  it('uses unique route names', () => {
    const routes = navigationItems.map((item) => item.route)
    expect(new Set(routes).size).toBe(routes.length)
  })

  it('omits desktop-only destinations on mobile', () => {
    const mobileRoutes = getNavigationItems({ mobile: true }).map(
      (item) => item.route,
    )
    expect(mobileRoutes).not.toContain('Dashboard')
    expect(mobileRoutes).not.toContain('Calendar')
    expect(mobileRoutes).toContain('Leads')
  })

  it('defines the grouped collapsible sections correctly', () => {
    expect(navigationSections.map((s) => s.name)).toEqual([
      'Data',
      'Outreach',
      'Sales Pipeline',
    ])

    const dataSection = navigationSections.find((s) => s.name === 'Data')
    expect(dataSection.items.map((i) => i.label)).toEqual([
      'Contacts',
      'Organizations',
      'Import',
      'Daily Allocation',
    ])

    const outreachSection = navigationSections.find((s) => s.name === 'Outreach')
    expect(outreachSection.items.map((i) => i.label)).toEqual(['My Task'])

    const salesSection = navigationSections.find(
      (s) => s.name === 'Sales Pipeline',
    )
    expect(salesSection.items.map((i) => i.label)).toEqual(['Leads', 'Deals'])
  })
})
