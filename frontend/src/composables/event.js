import { usersStore } from '@/stores/users'
import { dayjs, dayjsLocal, createListResource, getConfig } from 'frappe-ui'
import { sameArrayContents } from '@/utils'
import { computed, ref } from 'vue'
import { allTimeSlots } from '@/components/Calendar/utils'
import { createDialog } from '@/utils/dialogs'

// Lists events the usual way, plus ones linked to a lead or deal you can read,
// so a teammate's meeting on a lead shows on that lead (see crm/api/event.py)
export const EVENT_LIST_URL = 'crm.api.event.get_event_list'
// the server's cap (MAX_EVENT_ROWS in crm/api/event.py)
const MAX_EVENT_ROWS = 2000

// Event times are saved in the system timezone and shown in the user's, as tasks
// are. An all-day event holds only its day, so it isn't shifted.
export function eventTime(value, allDay = false) {
  return allDay ? dayjs(value) : dayjsLocal(value)
}

export function toSystemTime(localValue, allDay = false) {
  const systemTimezone = getConfig('systemTimezone')
  if (allDay || !systemTimezone) return localValue
  const localTimezone =
    getConfig('localTimezone') ||
    Intl.DateTimeFormat().resolvedOptions().timeZone
  return dayjs
    .tz(localValue, localTimezone)
    .tz(systemTimezone)
    .format('YYYY-MM-DD HH:mm:ss')
}

export const showEventModal = ref(false)
export const activeEvent = ref(null)

export function useEvent({
  doctype,
  docname,
  filters = null,
  participants = true,
  notifications = true,
}) {
  const { getUser } = usersStore()

  if (!filters) {
    if (doctype && docname) {
      filters = {
        reference_doctype: doctype,
        reference_docname: docname,
      }
    } else {
      filters = {}
    }
  }

  const eventsResource = createListResource({
    doctype: 'Event',
    url: EVENT_LIST_URL,
    cache: ['calendar-events', docname],
    fields: [
      'name',
      'status',
      'subject',
      'description',
      'starts_on',
      'ends_on',
      'all_day',
      'event_type',
      'location',
      'google_meet_link',
      'color',
      'attending',
      'owner',
      'reference_doctype',
      'reference_docname',
      'creation',
    ],
    filters: filters,
    auto: true,
    pageLength: 50,
    orderBy: 'creation desc',
  })

  const eventParticipantsResource = createListResource({
    doctype: 'Event Participants',
    url: EVENT_LIST_URL,
    fields: ['*'],
    parent: 'Event',
    pageLength: MAX_EVENT_ROWS,
  })

  const eventNotificationsResource = createListResource({
    doctype: 'Event Notifications',
    url: EVENT_LIST_URL,
    fields: ['*'],
    parent: 'Event',
    pageLength: MAX_EVENT_ROWS,
  })

  const events = computed(() => {
    if (!eventsResource.data) return []
    const eventNames = eventsResource.data.map((e) => e.name)

    // participants
    if (participants) {
      if (
        !eventParticipantsResource.data?.length ||
        eventsParticipantIsUpdated(eventNames)
      ) {
        eventParticipantsResource.update({
          filters: {
            parenttype: 'Event',
            parentfield: 'event_participants',
            parent: ['in', eventNames],
          },
        })
      } else {
        eventsResource.data.forEach((event) => {
          if (typeof event.owner !== 'object') {
            event.owner = {
              label: getUser(event.owner).full_name,
              image: getUser(event.owner).user_image,
              name: event.owner,
            }
          }

          event.event_participants = [
            ...eventParticipantsResource.data.filter(
              (participant) => participant.parent === event.name,
            ),
          ]

          event.participants = [
            event.owner,
            ...eventParticipantsResource.data
              .filter((participant) => participant.parent === event.name)
              .map((participant) => ({
                label:
                  getUser(participant.email).full_name || participant.email,
                image: getUser(participant.email).user_image || '',
                name: participant.email,
              })),
          ]
        })
      }
    }

    // notifications
    if (notifications) {
      if (!eventNotificationsResource.data?.length) {
        eventNotificationsResource.update({
          filters: {
            parenttype: 'Event',
            parentfield: 'notifications',
            parent: ['in', eventNames],
          },
        })
      } else {
        eventsResource.data.forEach((event) => {
          event.notifications = [
            ...eventNotificationsResource.data.filter(
              (notification) => notification.parent === event.name,
            ),
          ]
        })
      }
    }

    return eventsResource.data
  })

  function eventsParticipantIsUpdated(eventNames) {
    const parentFilter = eventParticipantsResource.filters?.parent?.[1]

    if (eventNames.length && !sameArrayContents(parentFilter, eventNames))
      return true

    let d = eventsResource.setValue.data
    if (!d) return false

    let newParticipants = d.event_participants.map((p) => p.name)
    let oldParticipants = eventParticipantsResource.data
      .filter((p) => p.parent === d.name)
      .map((p) => p.name)

    return !sameArrayContents(newParticipants, oldParticipants)
  }

  const startEndTime = (
    startTime,
    endTime,
    isFullDay = false,
    format = 'h:mm a',
  ) => {
    if (isFullDay) return __('All Day')
    const start = eventTime(startTime)
    const end = eventTime(endTime)

    return `${start.format(format)} - ${end.format(format)}`
  }

  const startDate = (
    startTime,
    format = 'ddd, D MMM YYYY',
    isFullDay = false,
  ) => eventTime(startTime, isFullDay).format(format)

  return {
    eventsResource,
    eventParticipantsResource,
    events,
    startEndTime,
    startDate,
  }
}

export function normalizeParticipants(list = []) {
  const seen = new Set()
  const out = []
  for (const a of list || []) {
    if (!a?.email || seen.has(a.email)) continue
    seen.add(a.email)
    out.push({
      email: a.email,
      reference_doctype: a.reference_doctype || 'Contact',
      reference_docname: a.reference_docname || '',
    })
  }
  return out
}

export function formatDuration(mins) {
  if (mins < 60) return __('{0} mins', [mins])
  let hours = mins / 60
  if (hours % 1 !== 0 && hours % 1 !== 0.5) {
    hours = hours.toFixed(2)
  }
  if (Number.isInteger(hours)) {
    return hours === 1 ? __('1 hr') : __('{0} hrs', [hours])
  }
  return `${hours} hrs`
}

export function buildEndTimeOptions(fromTime) {
  const timeSlots = allTimeSlots()
  if (!fromTime) return timeSlots
  const startIndex = timeSlots.findIndex((o) => o.value > fromTime)
  if (startIndex === -1) return []
  const [fh, fm] = fromTime.split(':').map((n) => parseInt(n))
  const fromTotal = fh * 60 + fm
  return timeSlots.slice(startIndex).map((o) => {
    const [th, tm] = o.value.split(':').map((n) => parseInt(n))
    const toTotal = th * 60 + tm
    const duration = toTotal - fromTotal
    return { ...o, label: `${o.label} (${formatDuration(duration)})` }
  })
}

export function computeAutoToTime(fromTime) {
  if (!fromTime) return ''
  const [hour, minute] = fromTime.split(':').map((n) => parseInt(n))
  let nh = hour + 1
  let nm = minute
  if (nh >= 24) {
    nh = 23
    nm = 59
  }
  return `${String(nh).padStart(2, '0')}:${String(nm).padStart(2, '0')}`
}

// Sets a start or end time and returns an error, leaving the end as it was if
// the change would make the meeting end before it starts.
export function changeTime(event, time, isStart = false) {
  const { toDate, toTime } = event
  if (isStart) {
    event.fromTime = time
    if (!event.toTime || event.toTime <= time) {
      event.toTime = computeAutoToTime(time)
    }
  } else {
    event.toTime = time
  }
  const days = dayjs(toDate).diff(dayjs(event.fromDate), 'day') || 0
  if (event.fromTime && event.toTime && days <= 1) {
    event.toDate = endDateFor(event.fromDate, event.fromTime, event.toTime)
  }
  const { error } = validateTimeRange(event)
  if (error) Object.assign(event, { toDate, toTime })
  return error
}

export function endDateFor(fromDate, fromTime, toTime) {
  if (toTime > fromTime) return fromDate
  return dayjs(fromDate).add(1, 'day').format('YYYY-MM-DD')
}

// Moving a meeting to another day keeps how many days it spans.
export function spanFrom(event, fromDate) {
  const days = dayjs(event.toDate).diff(dayjs(event.fromDate), 'day') || 0
  return dayjs(fromDate).add(days, 'day').format('YYYY-MM-DD')
}

export function validateTimeRange({
  fromDate,
  toDate,
  fromTime,
  toTime,
  isFullDay,
}) {
  if (isFullDay) return { valid: true, error: null }
  if (!fromTime || !toTime) {
    return { valid: false, error: __('Start & End Time Are Required') }
  }
  const start = dayjs(fromDate + ' ' + fromTime)
  // a meeting can end the next day, as one seen from another timezone often does
  const end = dayjs((toDate || fromDate) + ' ' + toTime)
  if (!start.isValid() || !end.isValid()) {
    return { valid: false, error: __('Invalid Start Or End Time') }
  }
  if (end.diff(start, 'minute') <= 0) {
    return { valid: false, error: __('End Time Should Be After Start Time') }
  }
  return { valid: true, error: null }
}

export function parseEventDoc(doc) {
  if (!doc) return {}
  const { getUser } = usersStore()

  return {
    id: doc.name,
    title: doc.subject,
    description: doc.description,
    status: doc.status,
    fromDate: eventTime(doc.starts_on, doc.all_day).format('YYYY-MM-DD'),
    toDate: eventTime(doc.ends_on, doc.all_day).format('YYYY-MM-DD'),
    fromTime: eventTime(doc.starts_on, doc.all_day).format('HH:mm'),
    toTime: eventTime(doc.ends_on, doc.all_day).format('HH:mm'),
    isFullDay: doc.all_day,
    eventType: doc.event_type,
    // the Meet link is shown, not saved: saving it as the location would pin it there
    location: doc.location || '',
    meetLink: doc.google_meet_link || '',
    color: doc.color,
    attending: doc.attending,
    referenceDoctype: doc.reference_doctype,
    referenceDocname: doc.reference_docname,
    event_participants: doc.event_participants || [],
    notifications: doc.notifications || [],
    owner: doc.owner
      ? {
          label: getUser(doc.owner).full_name,
          image: getUser(doc.owner).user_image,
          value: doc.owner,
        }
      : null,
  }
}

// A meeting booked from a booking page emails its guest when it's moved or
// deleted (crm.api.booking.sync_booking_from_event), so the CRM says so first.
// `booking` is { guest, startsOn, endsOn } as the meeting was loaded.

export function bookingOf(doc) {
  return doc?.booking_guest
    ? { guest: doc.booking_guest, startsOn: doc.starts_on, endsOn: doc.ends_on }
    : null
}

export function movesBooking(booking, { fromDate, fromTime, toDate, toTime }) {
  if (!booking) return false
  // the booking's times are system time, the edited ones the CRM user's, which
  // needn't be the browser's, so compare both as system time
  const same = (a, b) => dayjs(a).isSame(dayjs(toSystemTime(b)), 'minute')
  return (
    !same(booking.startsOn, `${fromDate} ${fromTime}`) ||
    !same(booking.endsOn, `${toDate || fromDate} ${toTime}`)
  )
}

export function confirmBookingMove(booking, onConfirm, onCancel = () => {}) {
  let confirmed = false
  createDialog({
    title: __('Move this meeting?'),
    message: __(
      '{0} booked this time from a booking page and will get an email with the new time.',
      [booking.guest],
    ),
    actions: [
      {
        label: __('Move and email'),
        variant: 'solid',
        onClick: (close) => {
          confirmed = true
          close()
          onConfirm()
        },
      },
    ],
    onClose: () => !confirmed && onCancel(),
  })
}

export function deleteEventMessage(booking) {
  return booking
    ? __(
        'This cancels the booking, and {0} will get an email saying the meeting is cancelled.',
        [booking.guest],
      )
    : __('Are you sure you want to delete this event?')
}
