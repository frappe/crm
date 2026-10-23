import { catalog, isRegistered, newItem } from '@/components/Home/widgets'

const Component = {}

const registry = [
  { key: 'replies_waiting', size: { w: 10, h: 8 }, component: Component },
  { key: 'my_tasks', size: { w: 10, h: 8 } },
  {
    key: 'team_overview',
    size: { w: 20, h: 8 },
    managerOnly: true,
    component: Component,
  },
]

const item = (name, y = 0, h = 8) => ({
  name,
  config: {},
  layout: { x: 0, y, w: 10, h, i: name },
})

describe('home widget catalog', () => {
  it('offers only widgets with a component', () => {
    expect(isRegistered('replies_waiting', registry)).toBe(true)
    expect(isRegistered('my_tasks', registry)).toBe(false)
    expect(isRegistered('sales_trend', registry)).toBe(false)
  })

  it('hides manager widgets from agents', () => {
    const keys = (manager) =>
      catalog({ manager, items: [] }, registry).map((w) => w.key)
    expect(keys(false)).toEqual(['replies_waiting'])
    expect(keys(true)).toEqual(['replies_waiting', 'team_overview'])
  })

  it('leaves out widgets already on the grid', () => {
    const offered = catalog(
      { manager: true, items: [item('replies_waiting')] },
      registry,
    )
    expect(offered.map((w) => w.key)).toEqual(['team_overview'])
  })

  it('is empty with an empty registry', () => {
    expect(catalog({ manager: true, items: [] }, [])).toEqual([])
  })
})

describe('newItem', () => {
  it('adds the widget below the grid at its default size', () => {
    const widget = registry[2]
    expect(newItem(widget, [item('a', 0, 8), item('b', 8, 4)])).toEqual({
      name: 'team_overview',
      config: {},
      layout: { x: 0, y: 12, w: 20, h: 8, i: 'team_overview' },
    })
  })

  it('starts at the top of an empty grid', () => {
    expect(newItem(registry[0], []).layout.y).toBe(0)
  })
})
