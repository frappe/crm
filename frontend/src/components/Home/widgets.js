import { defineAsyncComponent } from 'vue'

const lazy = (name) =>
  defineAsyncComponent(() => import(`./Widgets/${name}.vue`))

// Keys match WIDGETS in home_layout.py; sizes are DashboardGrid units (20 columns, 42px rows,
// 16px gutter), sized to fit content: header 44 + 6 rows × 32 + footer 40 ≤ 7 × 42 − 16.
// Team overview fits a 32px column header and 9 members: 44 + 32 + 9 × 32 + 40 = 10 × 42 − 16.
export const widgets = [
  {
    key: 'replies_waiting',
    label: 'Replies waiting',
    size: { w: 10, h: 7 },
    component: lazy('RepliesWaiting'),
  },
  {
    key: 'follow_ups_due',
    label: 'Follow-ups due',
    size: { w: 10, h: 7 },
    component: lazy('FollowUpsDue'),
  },
  {
    key: 'upcoming_follow_ups',
    label: 'Upcoming follow-ups',
    size: { w: 10, h: 7 },
    component: lazy('UpcomingFollowUps'),
  },
  {
    key: 'assigned_to_me',
    label: 'Assigned to me',
    size: { w: 10, h: 7 },
    component: lazy('AssignedToMe'),
  },
  {
    key: 'recently_opened',
    label: 'Recently opened',
    size: { w: 10, h: 7 },
    component: lazy('RecentlyOpened'),
  },
  {
    key: 'no_next_step',
    label: 'No next step',
    size: { w: 10, h: 7 },
    component: lazy('NoNextStep'),
  },
  {
    key: 'my_tasks',
    label: 'My tasks',
    size: { w: 10, h: 7 },
    component: lazy('MyTasks'),
  },
  {
    key: 'team_overview',
    label: 'Team overview',
    size: { w: 20, h: 10 },
    managerOnly: true,
    component: lazy('TeamOverview'),
  },
  {
    key: 'team_replies_waiting',
    label: 'Team replies waiting',
    size: { w: 10, h: 7 },
    managerOnly: true,
    component: lazy('TeamRepliesWaiting'),
  },
  {
    key: 'team_overdue_follow_ups',
    label: 'Team overdue follow-ups',
    size: { w: 10, h: 7 },
    managerOnly: true,
    component: lazy('TeamOverdueFollowUps'),
  },
  {
    key: 'unassigned',
    label: 'Unassigned',
    size: { w: 10, h: 7 },
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
  return {
    name: widget.key,
    config: {},
    layout: { x: 0, y, ...widget.size, i: widget.key },
  }
}
