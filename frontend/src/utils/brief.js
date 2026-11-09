import { dayjs } from 'frappe-ui'
import { recordRoute, recordTitle, taskRecordRoute } from '@/utils/home'
import { isTaskOverdue } from '@/utils/task'

const WEEKS_FROM_DAYS = 21

export function waitedFor(since, now = dayjs()) {
  const days = dayjs(now).diff(dayjs(since), 'day')
  if (days >= 1) {
    return days === 1 ? __('1 day') : __('{0} days', [days])
  }
  const hours = Math.max(dayjs(now).diff(dayjs(since), 'hour'), 1)
  return hours === 1 ? __('1 hour') : __('{0} hours', [hours])
}

export function shortAge(since, now = dayjs()) {
  const days = dayjs(now).diff(dayjs(since), 'day')
  if (days < 1) return __('Today')
  if (days < WEEKS_FROM_DAYS) return __('{0} d', [days])
  return __('{0} wk', [Math.floor(days / 7)])
}

export function briefSummary({ count, team, flow }) {
  if (!count) return __('Nothing needs you today')
  const things = team
    ? count === 1
      ? __('Your team has 1 thing that needs you today')
      : __('Your team has {0} things that need you today', [count])
    : count === 1
      ? __('1 thing needs you today')
      : __('{0} things need you today', [count])
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
        label: __('{0} late', [shortAge(item.oldest_due, now)]),
        late: true,
      }
    case 'follow_up':
      return isTaskOverdue(item)
        ? {
            label: __('{0} late', [shortAge(item.due_date, now)]),
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
      return { name: 'Tasks' }
    case 'ownerless':
    case 'workload':
      return { name: 'Leads' }
    case 'new':
      return item.count > 1 ? { name: 'Leads' } : recordRoute(item)
    default:
      return recordRoute(item)
  }
}

export function replyRoute(item) {
  const tab = item.channel === 'whatsapp' ? '#whatsapp' : '#emails'
  return { ...recordRoute(item), hash: tab }
}

const ACTION_LABELS = {
  waiting: () => __('Reply'),
  new: () => __('Review'),
  ownerless: () => __('Assign'),
  overdue_person: () => __('View tasks'),
  workload: () => __('View leads'),
}

export function briefActionLabel(item) {
  return ACTION_LABELS[item.kind]?.()
}

export function briefActionRoute(item) {
  return item.kind === 'waiting' ? replyRoute(item) : briefRoute(item)
}

export function flowSessionUrl(session) {
  return `/flow/s/${encodeURIComponent(session)}`
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
