import { dayjs, dayjsLocal } from 'frappe-ui'
import {
  recordListRoute,
  recordRoute,
  recordTitle,
  taskRecordRoute,
} from '@/utils/home'
import { dueDay, isTaskOverdue } from '@/utils/task'

const WEEKS_FROM_DAYS = 21

// The server sends times in the system time zone, and `now` is given the same way.
function instant(at) {
  return at ? dayjsLocal(at) : dayjsLocal()
}

export function waitedFor(since, now) {
  const days = instant(now).diff(instant(since), 'day')
  if (days >= 1) {
    return days === 1 ? __('1 day') : __('{0} days', [days])
  }
  const hours = Math.max(instant(now).diff(instant(since), 'hour'), 1)
  return hours === 1 ? __('1 hour') : __('{0} hours', [hours])
}

export function shortAge(since, now) {
  const days = instant(now).diff(instant(since), 'day')
  return days < 1 ? __('Today') : dayAge(days)
}

function lateBy(since, now) {
  const hours = instant(now).diff(instant(since), 'hour')
  if (hours < 24) return __('{0} h', [Math.max(hours, 1)])
  return dayAge(Math.floor(hours / 24))
}

// An all-day follow-up is late from the day after its day, wherever the user is.
function allDayLateBy(task, now) {
  const today = dayjs(instant(now).format('YYYY-MM-DD'))
  return dayAge(today.diff(dayjs(dueDay(task)), 'day'))
}

function dayAge(days) {
  if (days < WEEKS_FROM_DAYS) return __('{0} d', [days])
  return __('{0} wk', [Math.floor(days / 7)])
}

const COUNT_CAP = 500

// Past a few hundred the exact number stops meaning anything to the reader.
export function briefCount(count) {
  return count > COUNT_CAP ? `${COUNT_CAP}+` : count
}

export function briefSummary({ count, team, flow }) {
  if (!count) return __('Nothing needs you today')
  const things = team
    ? count === 1
      ? __('Your team has 1 thing that needs you today')
      : __('Your team has {0} things that need you today', [briefCount(count)])
    : count === 1
      ? __('1 thing needs you today')
      : __('{0} things need you today', [briefCount(count)])
  return flow
    ? __('{0}. Or ask Flow to get something done.', [things])
    : `${things}.`
}

export function briefTitle(item, { name = (user) => user } = {}) {
  switch (item.kind) {
    case 'waiting':
      return __('Reply to {0}', [recordTitle(item)])
    case 'follow_up':
      return item.title
    case 'no_next_step':
      return __('Plan a follow-up for {0}', [recordTitle(item)])
    case 'new':
      return item.count > 1
        ? __('Contact {0} new leads', [item.count])
        : __('Contact {0}', [recordTitle(item)])
    case 'client':
      return item.owner
        ? __('{0} is waiting on {1}', [recordTitle(item), name(item.owner)])
        : __('{0} is waiting on a reply', [recordTitle(item)])
    case 'ownerless':
      return item.count === 1
        ? __('Assign 1 lead with no owner')
        : __('Assign {0} leads with no owner', [item.count])
    case 'overdue_person':
      return item.count === 1
        ? __('{0} has 1 overdue follow-up', [name(item.member)])
        : __('{0} has {1} overdue follow-ups', [name(item.member), item.count])
    case 'workload':
      return workloadTitle(item, name)
  }
}

function workloadTitle(item, name) {
  const member = name(item.member)
  if (item.past_response) {
    return item.behind === 1
      ? __('{0} has 1 record past response time', [member])
      : __('{0} has {1} records past response time', [member, item.behind])
  }
  return item.behind === 1
    ? __('{0} has 1 customer waiting over 2 days', [member])
    : __('{0} has {1} customers waiting over 2 days', [member, item.behind])
}

export function briefDetail(
  item,
  {
    name = (user) => user,
    formatDate = (date) => date,
    formatDue = (task) => task.due_date,
  } = {},
) {
  switch (item.kind) {
    case 'waiting':
    case 'client':
      return lastMessage(item, formatDate)
    case 'follow_up':
      return [
        __('Task due {0}', [formatDue(item)]),
        item.reference_title || item.reference_docname,
      ]
        .filter(Boolean)
        .join(' · ')
    case 'no_next_step':
      return __('{0} · no activity and no follow-up for {1}', [
        item.doctype === 'CRM Deal' ? __('Open deal') : __('Open lead'),
        waitedFor(item.idle_since),
      ])
    case 'new':
      return __('Assigned in the last 7 days · {0}', [item.names.join(', ')])
    case 'ownerless':
      return __('Waiting for someone to take them')
    case 'overdue_person':
      return __('Oldest was due {0}', [formatDate(item.oldest_due)])
    case 'workload':
      return item.lightest
        ? __('{0} has none and {1} open', [
            name(item.lightest),
            item.lightest_open,
          ])
        : ''
    default:
      return ''
  }
}

function lastMessage(item, formatDate) {
  const email = item.last_email
  if (email) {
    return __('Last email from {0} on {1}', [
      email.sender || email.sender_email,
      formatDate(email.date),
    ])
  }
  return item.channel === 'whatsapp' ? __('Last message on WhatsApp') : ''
}

const ICONS = {
  follow_up: 'lucide-calendar-clock',
  no_next_step: 'lucide-clock',
  new: 'lucide-user-plus',
  ownerless: 'lucide-user-plus',
}

export function briefIcon(item) {
  if (item.channel === 'whatsapp') return 'lucide-message-circle'
  return ICONS[item.kind] || 'lucide-mail'
}

export function briefPerson(item) {
  if (item.kind === 'client') return item.owner
  if (item.kind === 'workload' || item.kind === 'overdue_person')
    return item.member
  return null
}

export function briefBadge(item) {
  if (item.kind !== 'workload' && item.past_response)
    return { label: __('Past SLA'), theme: 'red' }
  if (item.kind === 'follow_up' && item.priority === 'High')
    return { label: __('High'), theme: 'orange' }
  return null
}

export function briefAge(item, now) {
  switch (item.kind) {
    case 'waiting':
      return { label: shortAge(item.awaiting_reply_since, now) }
    case 'client':
      return { label: shortAge(item.waiting_since, now) }
    case 'no_next_step':
      return { label: shortAge(item.idle_since, now) }
    case 'new':
      return { label: shortAge(item.assigned_at, now) }
    case 'ownerless':
      return { label: shortAge(item.since, now) }
    case 'overdue_person':
      return {
        label: __('{0} late', [lateBy(item.oldest_due, now)]),
        late: true,
      }
    case 'follow_up':
      return isTaskOverdue(item)
        ? {
            label: __('{0} late', [
              item.all_day
                ? allDayLateBy(item, now)
                : lateBy(item.due_date, now),
            ]),
            late: true,
          }
        : { label: __('Due today') }
    default:
      return null
  }
}

export function briefRoute(item) {
  switch (item.kind) {
    case 'follow_up':
      return taskRecordRoute(item)
    case 'overdue_person':
      return { name: 'Tasks', query: memberQuery('overdue', item) }
    case 'workload':
      return {
        ...recordListRoute(item.doctype),
        query: { ...memberQuery('behind', item), brief_doctype: item.doctype },
      }
    case 'ownerless':
      return { name: 'Leads' }
    case 'new':
      return item.count > 1 ? { name: 'Leads' } : recordRoute(item)
    default:
      return recordRoute(item)
  }
}

function memberQuery(list, item) {
  return { brief_list: list, brief_tab: 'team', brief_member: item.member }
}

export function replyRoute(item) {
  const tab = item.channel === 'whatsapp' ? '#whatsapp' : '#emails'
  return { ...recordRoute(item), hash: tab }
}

const ACTIONS = {
  waiting: { label: () => __('Reply'), icon: 'lucide-reply' },
  new: { label: () => __('Review'), icon: 'lucide-eye' },
  ownerless: { label: () => __('Assign'), icon: 'lucide-user-plus' },
  overdue_person: {
    label: () => __('View tasks'),
    icon: 'lucide-square-check',
  },
  workload: { label: workloadActionLabel, icon: 'lucide-user' },
}

// The link opens one record type, so name the count when the other type is left out.
function workloadActionLabel(item) {
  const deals = item.doctype === 'Deal'
  if (!item.linked || item.linked >= item.behind)
    return deals ? __('View deals') : __('View leads')
  if (item.linked === 1) return deals ? __('View 1 deal') : __('View 1 lead')
  return deals
    ? __('View {0} deals', [item.linked])
    : __('View {0} leads', [item.linked])
}

export function briefActionLabel(item) {
  return ACTIONS[item.kind]?.label(item)
}

export function briefActionIcon(item) {
  return ACTIONS[item.kind]?.icon
}

export function briefActionRoute(item) {
  return item.kind === 'waiting' ? replyRoute(item) : briefRoute(item)
}

export const BRIEF_QUERY = 'brief'

const MORE_LISTS = [
  {
    doctype: 'CRM Lead',
    page: 'Leads',
    label: (n) => (n === 1 ? __('1 more lead') : __('{0} more leads', [n])),
  },
  {
    doctype: 'CRM Deal',
    page: 'Deals',
    label: (n) => (n === 1 ? __('1 more deal') : __('{0} more deals', [n])),
  },
  {
    doctype: 'CRM Task',
    page: 'Tasks',
    label: (n) => (n === 1 ? __('1 more task') : __('{0} more tasks', [n])),
  },
]

// What an empty brief can still point to: the team's brief, then older items.
export function briefEmptyLine({ tab, isManager, counts = {}, older = {} }) {
  if (tab === 'mine' && isManager && counts.team > 0) {
    return {
      text: __('Your team has {0} things to look at.', [
        briefCount(counts.team),
      ]),
      team: true,
    }
  }
  const hasOlder = Object.keys(older.conversations || {}).length || older.tasks
  return {
    text: hasOlder
      ? __('Older items are waiting below if you have time.')
      : __('New replies and follow-ups will show up here.'),
    team: false,
  }
}

export function briefMoreLinks(more = {}) {
  return MORE_LISTS.filter(({ doctype }) => more[doctype]?.length).map(
    ({ doctype, page, label }) => ({
      label: label(more[doctype].length),
      route: { name: page, query: { [BRIEF_QUERY]: more[doctype].join(',') } },
    }),
  )
}

export const BRIEF_LIST_QUERY = [
  'brief_list',
  'brief_tab',
  'brief_doctype',
  'brief_member',
]
export const OLDER_LISTS = ['conversations', 'tasks']

const OLDER_CONVERSATIONS = [
  {
    doctype: 'Lead',
    label: (n) =>
      n === 1
        ? __('1 older lead conversation')
        : __('{0} older lead conversations', [briefCount(n)]),
  },
  {
    doctype: 'Deal',
    label: (n) =>
      n === 1
        ? __('1 older deal conversation')
        : __('{0} older deal conversations', [briefCount(n)]),
  },
]

function olderConversationsLabel(n) {
  return n === 1
    ? __('1 older conversation')
    : __('{0} older conversations', [briefCount(n)])
}

function olderTasksLabel(n) {
  return n === 1 ? __('1 older task') : __('{0} older tasks', [briefCount(n)])
}

// With Leads & Deals, each type gets its own link, as each opens its own list.
export function briefOlderLinks({ older = {}, doctype = 'Both', tab } = {}) {
  const links = OLDER_CONVERSATIONS.filter(
    (list) => older.conversations?.[list.doctype] > 0,
  ).map((list) => {
    const count = older.conversations[list.doctype]
    return {
      label:
        doctype === 'Both' ? list.label(count) : olderConversationsLabel(count),
      route: {
        ...recordListRoute(list.doctype),
        query: {
          brief_list: 'conversations',
          brief_tab: tab,
          brief_doctype: list.doctype,
        },
      },
    }
  })
  if (older.tasks > 0) {
    links.push({
      label: olderTasksLabel(older.tasks),
      route: { name: 'Tasks', query: { brief_list: 'tasks', brief_tab: tab } },
    })
  }
  return links
}

export function briefListQuery(query) {
  const {
    brief_list: kind,
    brief_tab: tab,
    brief_doctype: doctype,
    brief_member: member,
  } = query
  if (!kind || !tab) return null
  return Object.fromEntries(
    Object.entries({ kind, tab, doctype, member }).filter(([, v]) => v),
  )
}

export function briefRecordNames(query) {
  return String(query[BRIEF_QUERY] || '')
    .split(',')
    .filter(Boolean)
}

export function flowSessionUrl(session) {
  return `/flow/s/${encodeURIComponent(session)}`
}

// In the page's Flow panel, as Cmd/Ctrl+I opens it. Frappe adds the panel only for Flow users on
// versions that have it, so anything that goes wrong opens the full Flow page instead.
// Returns whether the panel took it.
export function openFlowSession(
  session,
  { flow = window.flow, assign = (url) => window.location.assign(url) } = {},
) {
  try {
    flow.open({ session })
    return true
  } catch {
    assign(flowSessionUrl(session))
    return false
  }
}

export function askFlowChips({ team, repliesWaiting = 0, now = dayjs() }) {
  if (team) {
    return [
      __('Who on my team is behind on replies?'),
      __("Summarise this week's pipeline"),
      __('Which deals have stalled?'),
    ]
  }
  const chips = [
    __('How did my pipeline do in {0}?', [
      dayjs(now).subtract(1, 'month').format('MMMM'),
    ]),
    __('What should I work on first?'),
  ]
  if (repliesWaiting === 1)
    chips.unshift(__('Draft a reply for the customer waiting on me'))
  if (repliesWaiting > 1)
    chips.unshift(
      __('Draft replies for the {0} customers waiting on me', [repliesWaiting]),
    )
  return chips
}
