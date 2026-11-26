import { describe, expect, it, vi } from 'vitest'

vi.mock('@/router', () => ({
  default: { hasRoute: (name) => name !== 'Dashboard' },
}))

import {
  add,
  doctypeRefusal,
  drop,
  isChanged,
  moveBy,
  nest,
  remove,
  resetToDefault,
  toggleHidden,
  toPayload,
  update,
} from '@/components/CustomizeSidebar/rows'
import { getSidebarLayout } from '@/utils/navigation'

const link = (key, extra = {}) => ({
  key,
  type: 'Link',
  label: key,
  link_type: 'Built-in',
  link_to: key,
  ...extra,
})
const section = (key, extra = {}) => ({
  key,
  type: 'Section',
  label: key,
  collapsible: 1,
  ...extra,
})

const ROWS = [
  link('leads'),
  link('deals'),
  link('notes'),
  section('user:abc123'),
  link('site:prd001', {
    link_type: 'DocType',
    link_to: 'CRM Product',
    parent_key: 'user:abc123',
  }),
  section('public_views'),
  section('pinned_views'),
]
const keys = (rows) => rows.map((row) => row.key)

describe('Customize sidebar rows', () => {
  it('moves a row among its siblings only', () => {
    expect(keys(moveBy(ROWS, 'deals', -1)).slice(0, 3)).toEqual([
      'deals',
      'leads',
      'notes',
    ])
    expect(moveBy(ROWS, 'leads', -1)).toBe(ROWS)
    expect(keys(moveBy(ROWS, 'user:abc123', 1)).slice(3)).toEqual([
      'public_views',
      'user:abc123',
      'site:prd001',
      'pinned_views',
    ])
  })

  it('skips hidden siblings unless they are shown', () => {
    const rows = toggleHidden(ROWS, 'deals')
    const shown = (row) => !row.hidden
    expect(keys(moveBy(rows, 'notes', -1, shown)).slice(0, 3)).toEqual([
      'notes',
      'leads',
      'deals',
    ])
  })

  it('puts items only into a section a layer added', () => {
    expect(
      nest(ROWS, 'leads', 'user:abc123').find((row) => row.key === 'leads')
        .parent_key,
    ).toBe('user:abc123')
    expect(nest(ROWS, 'leads', 'public_views')).toMatch(/fills itself/)
    expect(nest(ROWS, 'user:abc123', 'public_views')).toMatch(/main list/)
    expect(drop(ROWS, 'notes', 'pinned_views')).toMatch(/fills itself/)
  })

  it('keeps the main list above every section', () => {
    const dropped = drop(ROWS, 'site:prd001', 'leads')
    expect(keys(dropped).slice(0, 2)).toEqual(['site:prd001', 'leads'])
    expect(drop(ROWS, 'user:abc123', 'leads')).toMatch(/below the main list/)
    expect(keys(drop(ROWS, 'pinned_views', 'user:abc123')).slice(3)).toEqual([
      'pinned_views',
      'user:abc123',
      'site:prd001',
      'public_views',
    ])
  })

  it('adds a section before Public Views and a DocType into the selected section', () => {
    const withSection = add(ROWS, section('user:new001'))
    expect(keys(withSection).slice(-3)).toEqual([
      'user:new001',
      'public_views',
      'pinned_views',
    ])
    const withDoctype = add(
      ROWS,
      link('user:new002', { link_type: 'DocType' }),
      'user:abc123',
    )
    expect(keys(withDoctype).slice(3, 6)).toEqual([
      'user:abc123',
      'site:prd001',
      'user:new002',
    ])
  })

  it('deletes only own rows, and a deleted section returns its items to the main list', () => {
    expect(remove(ROWS, 'leads', 'user')).toMatch(/Hide it instead/)
    expect(remove(ROWS, 'site:prd001', 'user')).toMatch(/Hide it instead/)
    const rows = remove(ROWS, 'user:abc123', 'user')
    expect(keys(rows)).toEqual([
      'leads',
      'deals',
      'notes',
      'site:prd001',
      'public_views',
      'pinned_views',
    ])
    expect(rows.find((row) => row.key === 'site:prd001').parent_key).toBeNull()
  })

  it('lets an inherited row change only its presentation', () => {
    const rows = update(
      ROWS,
      'leads',
      { label: 'Prospects', link_to: 'Other' },
      'user',
    )
    expect(rows[0]).toMatchObject({ label: 'Prospects', link_to: 'leads' })
    const below = [link('leads', { icon: 'star' })]
    expect(update(ROWS, 'leads', { icon: '' }, 'user', below)[0].icon).toBe(
      'star',
    )
  })

  it('refuses a DocType a built-in page or another row already opens', () => {
    const builtIns = { 'CRM Lead': 'Leads' }
    expect(doctypeRefusal(ROWS, 'CRM Lead', builtIns)).toBe(
      'Leads already opens CRM Lead.',
    )
    expect(doctypeRefusal(ROWS, 'CRM Product', builtIns)).toBe(
      'CRM Product is already in the sidebar, as site:prd001.',
    )
    expect(
      doctypeRefusal(ROWS, 'CRM Product', builtIns, 'site:prd001'),
    ).toBeNull()
  })

  it('ignores markers when telling a change and when saving', () => {
    const marked = ROWS.map((row) => ({ ...row, no_access: 1 }))
    expect(isChanged(ROWS, marked)).toBe(false)
    expect(toPayload(marked)[0]).not.toHaveProperty('no_access')
    expect(isChanged(ROWS, toggleHidden(ROWS, 'deals'))).toBe(true)
  })

  it('resets to the layer below, marking what the site hid', () => {
    const below = [link('leads'), link('deals', { hidden: 1 })]
    const rows = resetToDefault(ROWS, below, 'user')
    expect(rows[1].hidden_by).toBe('site')
  })
})

describe('Sidebar layout', () => {
  const today = [
    'home',
    'dashboard',
    'leads',
    'deals',
    'contacts',
    'organizations',
    'notes',
    'tasks',
    'calendar',
    'call_logs',
  ].map((key) => ({ key, type: 'Link', label: key, link_type: 'Built-in' }))

  it('draws the built-in pages that have a route, and desktop-only ones only on desktop', () => {
    const { main } = getSidebarLayout(today)
    expect(main.map((entry) => entry.key)).toEqual([
      'Home',
      'Leads',
      'Deals',
      'Contacts',
      'Organizations',
      'Notes',
      'Tasks',
      'Calendar',
      'Call Logs',
    ])
    const mobile = getSidebarLayout(today, { mobile: true }).main
    expect(mobile.map((entry) => entry.key)).not.toContain('Calendar')
  })

  it('keeps custom sections with their items, and leaves DocType items out until they have a route', () => {
    const items = [
      ...today,
      {
        key: 'user:abc123',
        type: 'Section',
        label: 'Setup',
        collapsible: 1,
        keep_closed: 1,
      },
      {
        key: 'tasks2',
        type: 'Link',
        link_type: 'Built-in',
        parent_key: 'user:abc123',
      },
      {
        key: 'user:prd001',
        type: 'Link',
        link_type: 'DocType',
        link_to: 'CRM Product',
        parent_key: 'user:abc123',
      },
      {
        key: 'public_views',
        type: 'Section',
        label: 'Public Views',
        collapsible: 1,
      },
    ]
    const { sections } = getSidebarLayout(items)
    expect(
      sections.map((entry) => [entry.key, entry.opened, entry.fillsFrom]),
    ).toEqual([
      ['user:abc123', false, null],
      ['public_views', true, 'public_views'],
    ])
    expect(sections[0].links).toEqual([])
  })
})
