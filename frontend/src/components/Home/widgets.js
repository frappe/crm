import { defineAsyncComponent } from 'vue'

const lazy = (name) =>
  defineAsyncComponent(() => import(`./Widgets/${name}.vue`))

// Keys match WIDGETS in home_layout.py; sizes are DashboardGrid units (20 columns, 42px rows,
// 16px gutter), sized to fit content. List rows are 40px with 1px dividers:
// border 2 + title and subtitle 75 + column header 40 + 6 rows (245) + footer 32 = 394 ≤ 10 × 42 − 16.
// Team replies waiting has five columns, so it defaults to full width. Task tables need the full
// width for their title, record and assignee, so minW stops them from being resized narrower.
export const widgets = [
  {
    key: 'tasks',
    label: 'My tasks',
    size: { w: 20, h: 10 },
    minW: 20,
    component: lazy('Tasks'),
  },
  {
    key: 'leads_and_deals',
    label: 'Needs your attention',
    size: { w: 10, h: 10 },
    component: lazy('LeadsAndDeals'),
  },
  {
    key: 'leads',
    label: 'Leads needing attention',
    size: { w: 10, h: 10 },
    component: lazy('Leads'),
  },
  {
    key: 'deals',
    label: 'Deals needing attention',
    size: { w: 10, h: 10 },
    component: lazy('Deals'),
  },
  {
    key: 'recently_opened',
    label: 'Recent activity',
    size: { w: 10, h: 10 },
    component: lazy('RecentlyOpened'),
  },
  {
    key: 'no_next_step',
    label: 'Going cold',
    size: { w: 10, h: 10 },
    component: lazy('NoNextStep'),
  },
  {
    key: 'funnel_conversion',
    label: 'Sales funnel',
    size: { w: 20, h: 10 },
    component: lazy('FunnelConversion'),
  },
  {
    key: 'won_this_month',
    label: 'Won',
    size: { w: 10, h: 4 },
    component: lazy('WonThisMonth'),
  },
  {
    key: 'expected_revenue',
    label: 'Expected revenue',
    size: { w: 10, h: 4 },
    component: lazy('ExpectedRevenue'),
  },
  {
    key: 'top_open_deals',
    label: 'Top open deals',
    size: { w: 10, h: 10 },
    component: lazy('TopOpenDeals'),
  },
  {
    key: 'team_overview',
    label: 'Team workload',
    size: { w: 10, h: 10 },
    managerOnly: true,
    component: lazy('TeamOverview'),
  },
  {
    key: 'team_replies_waiting',
    label: 'Waiting on your team',
    size: { w: 20, h: 10 },
    managerOnly: true,
    component: lazy('TeamRepliesWaiting'),
  },
  {
    key: 'team_overdue_follow_ups',
    label: 'Missed follow-ups',
    size: { w: 20, h: 10 },
    minW: 20,
    managerOnly: true,
    component: lazy('TeamOverdueFollowUps'),
  },
  {
    key: 'unassigned',
    label: 'Needs an owner',
    size: { w: 10, h: 10 },
    managerOnly: true,
    component: lazy('Unassigned'),
  },
]

export function getWidget(key, registry = widgets) {
  return registry.find((widget) => widget.key === key)
}

export function isRegistered(key, registry = widgets) {
  return Boolean(getWidget(key, registry)?.component)
}

export function catalog({ manager, items }, registry = widgets) {
  const added = new Set(items.map((item) => item.name))
  return registry.filter(
    (widget) =>
      widget.component &&
      (manager || !widget.managerOnly) &&
      !added.has(widget.key),
  )
}

export function newItem(widget, items) {
  const y = Math.max(0, ...items.map(({ layout }) => layout.y + layout.h))
  return withMinWidth(
    {
      name: widget.key,
      config: {},
      layout: { x: 0, y, ...widget.size, i: widget.key },
    },
    [widget],
  )
}

// The grid reads minW from the layout; the server drops it on save.
export function withMinWidth(item, registry = widgets) {
  const minW = getWidget(item.name, registry)?.minW
  return minW ? { ...item, layout: { ...item.layout, minW } } : item
}

// The grid adds its own keys (moved, minW) to each layout, so only what the server stores counts.
export function persistedLayout(items) {
  return JSON.stringify(
    items.map(({ name, config, layout: { x, y, w, h } }) => ({
      name,
      config,
      layout: { x, y, w, h },
    })),
  )
}
