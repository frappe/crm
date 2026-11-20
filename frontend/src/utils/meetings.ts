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

function duration(minutes: number): string {
  const h = Math.floor(minutes / 60)
  const m = minutes % 60
  if (!h) return __('{0}m', [m])
  return m ? __('{0}h {1}m', [h, m]) : __('{0}h', [h])
}

// "23m left" while it's on, "in 25m" before it starts.
export function meetingCountdown(meeting: Meeting, now = dayjs()): string {
  if (meeting.all_day) return __('All day')
  if (isOngoing(meeting, now)) {
    const left = Math.max(1, dayjsLocal(meeting.ends_on).diff(now, 'minute'))
    return __('{0} left', [duration(left)])
  }
  const until = Math.max(1, dayjsLocal(meeting.starts_on).diff(now, 'minute'))
  return __('in {0}', [duration(until)])
}

// The first meeting still to come, or the one that's on now; all-day ones aren't featured.
export function nextMeeting<T extends Meeting>(
  meetings: T[],
  now = dayjs(),
): T | null {
  return meetings.find((m) => !m.all_day && !hasEnded(m, now)) || null
}

const PROVIDERS: [RegExp, string][] = [
  [/meet\.google\.com/, 'Google Meet'],
  [/zoom\.us/, 'Zoom'],
  [/teams\.microsoft\.com|teams\.live\.com/, 'Teams'],
]

// Where it happens: the room for an in-person meeting, else the video provider.
export function meetingPlace(meeting: Meeting): string | null {
  const link = meetingLink(meeting)
  if (!link) return meeting.location || null
  return (
    PROVIDERS.find(([pattern]) => pattern.test(link))?.[1] || __('Video call')
  )
}

export function meetingStart(meeting: Meeting): string {
  return meeting.all_day
    ? __('All day')
    : dayjsLocal(meeting.starts_on).format(TIME)
}
