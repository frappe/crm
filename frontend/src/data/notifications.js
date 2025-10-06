import { sessionStore } from '@/stores/session'
import { createListResource, dayjs } from 'frappe-ui'
import isBetween from 'dayjs/plugin/isBetween'
import { useStorage } from '@vueuse/core'
import { getUserSettings, useUserSettings } from '@/data/userSettings'
import { ref, computed } from 'vue'

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
          fromDate: dayjs(event.starts_on).format('YYYY-MM-DD'),
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
  const { save: saveUserSettings } = useUserSettings()
  const completedEvents = ref([])

  // Load user settings on initialization
  const loadNotificationSettings = async () => {
    try {
      const settings = await getUserSettings('Event', 'notifications')
      if (settings) {
        completedEvents.value = settings.completedEvents || []
      }
    } catch (error) {
      console.error('Error loading notification settings:', error)
    }
  }

  // Save completed events to user settings
  const saveNotificationSettings = async () => {
    try {
      await saveUserSettings('Event', 'notifications', {
        completedEvents: completedEvents.value,
        lastUpdated: dayjs().toISOString(),
      })
    } catch (error) {
      console.error('Error saving notification settings:', error)
    }
  }

  // Check if event has already been completed/acknowledged
  const isEventCompleted = (eventId) => completedEvents.value.includes(eventId)

  // Get active (non-completed) notification alerts
  const activeAlerts = computed(() => {
    return eventNotificationAlerts.value.filter(
      (alert) => !alert.completed && !isEventCompleted(alert.id),
    )
  })

  function handleEventNotification(event) {
    if (isEventCompleted(event.event_name)) return

    addEventNotificationAlert(event)
  }

  function addEventNotificationAlert(data) {
    // Don't add if already exists and not completed
    const existingAlert = eventNotificationAlerts.value.find(
      (alert) => alert.id === data.event_name && !alert.completed,
    )

    if (existingAlert) return

    eventNotificationAlerts.value.push({
      id: data.event_name,
      completed: false,
      notification: data,
      createdAt: dayjs().toISOString(),
    })
  }

  async function completeEventNotificationAlert(id) {
    let alert = eventNotificationAlerts.value.find((a) => a.id === id)
    if (alert) {
      alert.completed = true
    }

    // Add to completed events in user settings
    if (!completedEvents.value.includes(id)) {
      completedEvents.value.push(id)
      await saveNotificationSettings()
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

  async function clearCompletedEvents() {
    completedEvents.value = []
    await saveNotificationSettings()
  }

  loadNotificationSettings()

  return {
    eventNotificationAlerts,
    activeAlerts,
    completedEvents,
    isEventCompleted,
    handleEventNotification,
    addEventNotificationAlert,
    completeEventNotificationAlert,
    removeCompletedEventNotificationAlerts,
    clearAllEventNotificationAlerts,
    clearCompletedEvents,
    loadNotificationSettings,
    saveNotificationSettings,
  }
}
