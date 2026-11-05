import { dayjs, dayjsLocal, getConfig } from 'frappe-ui'

// Mirrors crm/fcrm/doctype/crm_task/rules.py: an all-day due_date holds only its day,
// unshifted by timezone; a timed due_date is an instant in system time.

const CLOSED_STATUSES = ['Done', 'Canceled']
const DAY = 'YYYY-MM-DD'

const FORMATS = {
  short: { allDay: 'D MMM', timed: 'D MMM, hh:mm a' },
  long: { allDay: 'ddd, MMM D, YYYY', timed: 'ddd, MMM D, YYYY | hh:mm a' },
}

export function isTaskOverdue(task) {
  if (!task?.due_date || CLOSED_STATUSES.includes(task.status)) return false
  if (task.all_day) return dueDay(task) < dayjsLocal().format(DAY)
  return dayjsLocal(task.due_date).isBefore(dayjs())
}

export function formatTaskDue(task, length = 'short') {
  if (!task?.due_date) return ''
  const format = FORMATS[length]
  if (task.all_day) return dayjs(dueDay(task)).format(format.allDay)
  return dayjsLocal(task.due_date).format(format.timed)
}

export function toAllDayDueDate(dueDate) {
  return dueDate ? dayjsLocal(dueDate).format(DAY) : dueDate
}

export function fromAllDayDueDate(dueDate) {
  if (!dueDate) return dueDate
  const midnight = `${dueDate.slice(0, 10)} 00:00:00`
  const systemTimezone = getConfig('systemTimezone')
  if (!systemTimezone) return midnight
  const localTimezone =
    getConfig('localTimezone') ||
    Intl.DateTimeFormat().resolvedOptions().timeZone
  return dayjs
    .tz(midnight, localTimezone)
    .tz(systemTimezone)
    .format('YYYY-MM-DD HH:mm:ss')
}

export function followUpPresets(now = dayjsLocal()) {
  const daysToMonday = (8 - now.day()) % 7 || 7
  return [
    { key: 'today', label: __('Today'), date: now },
    { key: 'tomorrow', label: __('Tomorrow'), date: now.add(1, 'day') },
    { key: 'in_3_days', label: __('In 3 days'), date: now.add(3, 'day') },
    {
      key: 'next_week',
      label: __('Next week'),
      date: now.add(daysToMonday, 'day'),
    },
  ].map((preset) => ({ ...preset, date: preset.date.format(DAY) }))
}

export function nextFollowUp(tasks = []) {
  return tasks
    .filter((task) => task.due_date && !CLOSED_STATUSES.includes(task.status))
    .sort((a, b) => dueSortKey(a).localeCompare(dueSortKey(b)))[0]
}

function dueSortKey(task) {
  if (task.all_day) return `${dueDay(task)} 00:00:00`
  return dayjsLocal(task.due_date).format('YYYY-MM-DD HH:mm:ss')
}

function dueDay(task) {
  return task.due_date.slice(0, 10)
}
