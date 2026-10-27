import { defineAsyncComponent } from 'vue'

const lazy = (name) =>
  defineAsyncComponent(() => import(`./Widgets/${name}.vue`))

// Keys match WIDGETS in home_layout.py; sizes are DashboardGrid units (20 columns, 42px rows,
// 16px gutter), sized to fit content. List rows are 40px with 1px dividers:
// border 2 + header 40 + 6 rows (245) + footer 32 = 319 ≤ 8 × 42 − 16.
// Team overview adds a 40px column header and shows 5 members: 2 + 40 + 40 + 204 + 32 = 318.
// Team replies waiting has five columns, so it defaults to full width. Task tables need the full
// width for their title, record and assignee, so minW stops them from being resized narrower.
export const widgets = [
  {
    key: 'replies_waiting',
    label: 'Replies waiting',
    size: { w: 10, h: 8 },
    component: lazy('RepliesWaiting'),
  },
  {
    key: 'follow_ups_due',
    label: 'Follow-ups due',
    size: { w: 20, h: 8 },
    minW: 20,
    component: lazy('FollowUpsDue'),
  },
  {
    key: 'upcoming_follow_ups',
    label: 'Upcoming follow-ups',
    size: { w: 20, h: 8 },
    minW: 20,
    component: lazy('UpcomingFollowUps'),
  },
  {
    key: 'assigned_to_me',
    label: 'Assigned to me',
    size: { w: 10, h: 8 },
    component: lazy('AssignedToMe'),
  },
  {
    key: 'recently_opened',
    label: 'Recently opened',
    size: { w: 10, h: 8 },
    component: lazy('RecentlyOpened'),
  },
  {
    key: 'no_next_step',
    label: 'No next step',
    size: { w: 10, h: 8 },
    component: lazy('NoNextStep'),
  },
  {
    key: 'my_tasks',
    label: 'My tasks',
    size: { w: 20, h: 8 },
    minW: 20,
    component: lazy('MyTasks'),
  },
  {
    key: 'team_overview',
    label: 'Team overview',
    size: { w: 10, h: 8 },
    managerOnly: true,
    component: lazy('TeamOverview'),
  },
  {
    key: 'team_replies_waiting',
    label: 'Team replies waiting',
    size: { w: 20, h: 8 },
    managerOnly: true,
    component: lazy('TeamRepliesWaiting'),
  },
  {
    key: 'team_overdue_follow_ups',
    label: 'Team overdue follow-ups',
    size: { w: 20, h: 8 },
    minW: 20,
    managerOnly: true,
    component: lazy('TeamOverdueFollowUps'),
  },
  {
    key: 'unassigned',
    label: 'Unassigned',
    size: { w: 10, h: 8 },
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
