import { defineAsyncComponent } from 'vue'

const lazy = (name) =>
  defineAsyncComponent(() => import(`./Widgets/${name}.vue`))

// Keys match WIDGETS in home_layout.py; sizes are DashboardGrid units (20 columns, 42px rows,
// 16px gutter), sized to fit content. List rows are 40px with 1px dividers:
// border 2 + title 40 + column header 40 + 6 rows (245) + footer 32 = 359 ≤ 9 × 42 − 16.
// Team replies waiting has five columns, so it defaults to full width. Task tables need the full
// width for their title, record and assignee, so minW stops them from being resized narrower.
export const widgets = [
  {
    key: 'tasks',
    label: 'Tasks',
    size: { w: 20, h: 9 },
    minW: 20,
    component: lazy('Tasks'),
  },
  {
    key: 'leads_and_deals',
    label: 'Leads & deals',
    size: { w: 10, h: 9 },
    component: lazy('LeadsAndDeals'),
  },
  {
    key: 'leads',
    label: 'Leads',
    size: { w: 10, h: 9 },
    component: lazy('Leads'),
  },
  {
    key: 'deals',
    label: 'Deals',
    size: { w: 10, h: 9 },
    component: lazy('Deals'),
  },
  {
    key: 'recently_opened',
    label: 'Recently opened',
    size: { w: 10, h: 9 },
    component: lazy('RecentlyOpened'),
  },
  {
    key: 'no_next_step',
    label: 'No next step',
    size: { w: 10, h: 9 },
    component: lazy('NoNextStep'),
  },
  {
    key: 'team_overview',
    label: 'Team overview',
    size: { w: 10, h: 9 },
    managerOnly: true,
    component: lazy('TeamOverview'),
  },
  {
    key: 'team_replies_waiting',
    label: 'Team replies waiting',
    size: { w: 20, h: 9 },
    managerOnly: true,
    component: lazy('TeamRepliesWaiting'),
  },
  {
    key: 'team_overdue_follow_ups',
    label: 'Team overdue follow-ups',
    size: { w: 20, h: 9 },
    minW: 20,
    managerOnly: true,
    component: lazy('TeamOverdueFollowUps'),
  },
  {
    key: 'unassigned',
    label: 'Unassigned',
    size: { w: 10, h: 9 },
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
