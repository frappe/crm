import { dayjs, dayjsLocal, getConfig } from 'frappe-ui'

// Mirrors crm/fcrm/doctype/crm_task/rules.py. An all-day due_date holds only its
// day, unshifted by any timezone; a timed due_date is an instant in system time.

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

function dueDay(task) {
  return task.due_date.slice(0, 10)
}
