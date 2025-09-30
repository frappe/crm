import { sessionStore } from '@/stores/session'
import { createListResource, dayjs } from 'frappe-ui'
import isBetween from 'dayjs/plugin/isBetween'
import { useStorage } from '@vueuse/core'

dayjs.extend(isBetween)

export const useEventNotifications = () => {
  const { user } = sessionStore()

  const events = createListResource({
    doctype: 'Event',
    fields: ['*'],
    filters: { status: 'Open', owner: user },
    auto: true,
    limit: 9999,
    orderBy: 'modified desc',
    transform: (d) => {
      return d.map((event) => {
        let type = 'upcoming'

        // Starting Now: Event is within [now - 5 min, now + 5 min]
        if (
          dayjs(event.starts_on).isBetween(
            dayjs().subtract(5, 'minute'),
            dayjs().add(5, 'minute'),
          )
        ) {
          type = 'startingNow'
        }
        // Upcoming: Event is greater than now + 5 min
        else if (dayjs(event.starts_on).isAfter(dayjs().add(5, 'minute'))) {
          type = 'upcoming'
        }
        // Overdue: Event is less than now - 5 min
        else if (
          dayjs(event.starts_on).isBefore(dayjs().subtract(5, 'minute'))
        ) {
          type = 'overdue'
        }

        const eventDate = dayjs(event.starts_on)
        const now = dayjs()
        let dateLabel

        if (eventDate.isSame(now, 'day')) {
          dateLabel = 'Today'
          if (type === 'startingNow') {
            dateLabel = 'Now'
          }
        } else if (eventDate.isSame(now.add(1, 'day'), 'day')) {
          dateLabel = 'Tomorrow'
        } else if (eventDate.isSame(now.subtract(1, 'day'), 'day')) {
          dateLabel = 'Yesterday'
        } else {
          dateLabel = eventDate.format('MMM D')
        }

        return {
          id: event.name,
          title: event.subject,
          date: dateLabel,
          fromTime: dayjs(event.starts_on).format('h:mm a'),
          toTime: dayjs(event.ends_on).format('h:mm a'),
          color: event.color,
          allDay: event.all_day,
          type,
        }
      })
    },
  })

  return { events }
}

const eventNotificationAlerts = useStorage('eventNotificationAlerts', [])

export const useEventNotificationAlert = () => {
  function addEventNotificationAlert(data) {
    eventNotificationAlerts.value.push({
      id: data.notification.name,
      completed: false,
      notification: data.notification,
    })
  }

  function completeEventNotificationAlert(id) {
    let alert = eventNotificationAlerts.value.find((a) => a.id === id)
    if (alert) {
      alert.completed = true
    }
  }

  function removeCompletedEventNotificationAlerts() {
    eventNotificationAlerts.value = eventNotificationAlerts.value.filter(
      (alert) => !alert.completed,
    )
  }

  function clearAllEventNotificationAlerts() {
    eventNotificationAlerts.value = []
  }

  return {
    eventNotificationAlerts,
    addEventNotificationAlert,
    completeEventNotificationAlert,
    removeCompletedEventNotificationAlerts,
    clearAllEventNotificationAlerts,
  }
}
