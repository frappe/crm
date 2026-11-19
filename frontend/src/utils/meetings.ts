import { dayjs, dayjsLocal } from 'frappe-ui'

export interface Meeting {
  name: string
  subject?: string
  starts_on: string
  ends_on?: string | null
  all_day?: 0 | 1 | boolean
  color?: string | null
  location?: string | null
  google_meet_link?: string | null
}

const TIME = 'h:mm a'

// Same rule as the calendar's event panel: the location wins, then the Meet link.
export function meetingLink(meeting: Meeting): string | null {
  const link = meeting.location || meeting.google_meet_link || ''
  return /^https?:\/\//.test(link) ? link : null
}

export function meetingTime(meeting: Meeting): string {
  if (meeting.all_day) return __('All day')
  const start = dayjsLocal(meeting.starts_on).format(TIME)
  if (!meeting.ends_on) return start
  return `${start} – ${dayjsLocal(meeting.ends_on).format(TIME)}`
}

// While a meeting is on, only its end matters: "until 9:45 am".
export function meetingUntil(meeting: Meeting): string {
  return __('until {0}', [dayjsLocal(meeting.ends_on).format(TIME)])
}

export function isOngoing(meeting: Meeting, now = dayjs()): boolean {
  if (meeting.all_day || !meeting.ends_on) return false
  return (
    !dayjsLocal(meeting.starts_on).isAfter(now) &&
    dayjsLocal(meeting.ends_on).isAfter(now)
  )
}

export function hasEnded(meeting: Meeting, now = dayjs()): boolean {
  if (meeting.all_day) return false
  return !dayjsLocal(meeting.ends_on || meeting.starts_on).isAfter(now)
}

// Opens the meeting in the calendar, on its day.
export function meetingRoute(meeting: Meeting) {
  const date = meeting.all_day
    ? dayjs(meeting.starts_on)
    : dayjsLocal(meeting.starts_on)
  return {
    name: 'Calendar',
    query: { eventId: meeting.name, date: date.format('YYYY-MM-DD') },
  }
}
