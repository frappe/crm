import { defineAsyncComponent } from 'vue'

const lazy = (name) =>
  defineAsyncComponent(() => import(`./Widgets/${name}.vue`))

// Keys match WIDGETS in home_layout.py; sizes are DashboardGrid units (20 columns, 42px rows,
// 16px gutter), sized to fit content. List rows are 40px with 1px dividers:
// border 2 + title and subtitle 75 + column header 40 + 6 rows (245) + footer 32 = 394 ≤ 10 × 42 − 16.
// Team replies waiting has five columns, so it defaults to full width. My tasks is 15 × 8 with 4 rows and can shrink to
// 12 columns, with two cards (4 rows high each) stacked beside it to match its height.
export const widgets = [
  {
    key: 'tasks',
    label: 'My tasks',
    icon: 'lucide-square-check',
    size: { w: 15, h: 8 },
    minW: 12,
    minH: 8,
    component: lazy('Tasks'),
  },
  {
    key: 'leads_and_deals',
    label: 'My leads and deals',
    icon: 'lucide-mail',
    size: { w: 10, h: 10 },
    component: lazy('LeadsAndDeals'),
  },
  {
    key: 'leads',
    label: 'My leads',
    icon: 'lucide-user',
    size: { w: 10, h: 10 },
    component: lazy('Leads'),
  },
  {
    key: 'deals',
    label: 'My deals',
    icon: 'lucide-handshake',
    size: { w: 10, h: 10 },
    component: lazy('Deals'),
  },
  {
    key: 'recently_opened',
    label: 'Recent activity',
    icon: 'lucide-clock',
    size: { w: 10, h: 10 },
    component: lazy('RecentlyOpened'),
  },
  {
    key: 'no_next_step',
    label: 'No next step',
    icon: 'lucide-calendar-x',
    size: { w: 10, h: 10 },
    component: lazy('NoNextStep'),
  },
  {
    key: 'funnel_conversion',
    label: 'Sales funnel',
    icon: 'lucide-filter',
    size: { w: 20, h: 10 },
    component: lazy('FunnelConversion'),
  },
  {
    key: 'won_this_month',
    label: 'Deals won',
    icon: 'lucide-trophy',
    size: { w: 5, h: 4 },
    component: lazy('WonThisMonth'),
  },
  {
    key: 'expected_revenue',
    label: 'Expected revenue',
    icon: 'lucide-trending-up',
    size: { w: 5, h: 4 },
    component: lazy('ExpectedRevenue'),
  },
  {
    key: 'top_open_deals',
    label: 'Largest open deals',
    icon: 'lucide-zap',
    size: { w: 10, h: 10 },
    component: lazy('TopOpenDeals'),
  },
  {
    key: 'team_overview',
    label: 'Team workload',
    icon: 'lucide-users',
    size: { w: 15, h: 10 },
    minH: 10,
    managerOnly: true,
    component: lazy('TeamOverview'),
  },
  {
    key: 'team_replies_waiting',
    label: 'Team replies waiting',
    icon: 'lucide-inbox',
    size: { w: 20, h: 10 },
    managerOnly: true,
    component: lazy('TeamRepliesWaiting'),
  },
  {
    key: 'overdue_and_unassigned',
    label: 'Overdue and unassigned',
    icon: 'lucide-calendar-clock',
    size: { w: 10, h: 10 },
    managerOnly: true,
    component: lazy('OverdueAndUnassigned'),
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
  return withMinSize(
    {
      name: widget.key,
      config: {},
      layout: { x: 0, y, ...widget.size, i: widget.key },
    },
    [widget],
  )
}

// The grid reads minW and minH from the layout; the server drops them on save.
export function withMinSize(item, registry = widgets) {
  const { minW, minH } = getWidget(item.name, registry) || {}
  if (!minW && !minH) return item
  const minimums = { ...(minW && { minW }), ...(minH && { minH }) }
  return { ...item, layout: { ...item.layout, ...minimums } }
}

// The grid adds its own keys (moved, minW, minH) to each layout, so only what the server stores counts.
export function persistedLayout(items) {
  return JSON.stringify(
    items.map(({ name, config, layout: { x, y, w, h } }) => ({
      name,
      config,
      layout: { x, y, w, h },
    })),
  )
}
