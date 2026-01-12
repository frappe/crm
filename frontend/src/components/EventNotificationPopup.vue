<template>
  <Teleport to="body">
    <div
      v-if="visibleAlerts.length > 0"
      class="fixed bottom-4 right-4 z-50 w-96"
    >
      <TransitionGroup name="popup" tag="div" class="space-y-2">
        <div
          v-for="alert in visibleAlerts"
          :key="alert.id"
          class="group flex flex-col relative bg-surface-cards rounded-lg drop-shadow-2xl shadow-sm"
        >
          <div class="flex justify-between items-center gap-1 p-3">
            <div class="flex items-stretch space-x-2">
              <div>
                <CalendarIcon class="size-4 text-cyan-500" />
              </div>
              <div class="flex flex-col text-base">
                <div
                  class="font-medium text-ink-gray-8 mb-1 cursor-pointer"
                  @click="openEvent(alert)"
                >
                  {{ alert.notification.subject || 'Event Notification' }}
                </div>
                <div class="text-ink-gray-6">
                  {{ formatEventTime(alert.notification) }}
                </div>
              </div>
            </div>

            <MultipleAvatar
              v-if="getParticipants(alert.notification)?.length > 0"
              :avatars="getParticipants(alert.notification)"
              size="md"
              @click="openEvent(alert)"
            />
          </div>
          <Button
            class="absolute -top-2 -left-2 shadow ring-inset !bg-surface-cards hover:!bg-surface-gray-1 text-ink-gray-3 !p-0 !size-5 rounded-full opacity-0 group-hover:opacity-100 transition-opacity"
            @click="completeAlert(alert.id)"
          >
            <FeatherIcon name="x" class="size-4 text-ink-gray-3 stroke-2" />
          </Button>
        </div>
      </TransitionGroup>
    </div>
  </Teleport>
</template>

<script setup>
import { useEventNotificationAlert } from '@/data/notifications'
import { usersStore } from '@/stores/users'
import { Button, dayjs } from 'frappe-ui'
import { computed, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const { getUser } = usersStore()

const {
  eventNotificationAlerts,
  completeEventNotificationAlert,
  removeCompletedEventNotificationAlerts,
} = useEventNotificationAlert()

const visibleAlerts = computed(() => {
  return eventNotificationAlerts.value.filter((alert) => !alert.completed)
})

function openEvent(e) {
  completeAlert(e.id)
  router.push({
    name: 'Calendar',
    query: {
      eventId: e.notification.event_name,
      date: dayjs(e.notification.starts_on).format('YYYY-MM-DD'),
    },
  })
}

function completeAlert(id) {
  completeEventNotificationAlert(id)

  setTimeout(() => removeCompletedEventNotificationAlerts(), 300)
}

function formatEventTime(notification) {
  if (notification.all_day_event) {
    return __('All Day')
  } else if (notification.starts_on) {
    const startTime = dayjs(notification.starts_on).format('h:mm a')
    const endTime = dayjs(notification.ends_on).format('h:mm a')
    return `${startTime} - ${endTime}`
  }
  return ''
}

function getParticipants(notification) {
  const participants = notification.event_participants?.map((p) => p) || []

  if (!participants.length) return []

  if (notification.owner && !participants.includes(notification.owner)) {
    participants.push(notification.owner)
  }

  return (
    participants.map((p) => {
      return {
        label: getUser(p).full_name || p,
        image: getUser(p).user_image || '',
        name: p,
      }
    }) || []
  )
}

let checkInterval

onMounted(() => {
  checkInterval = setInterval(() => {}, 10000) // Check every 10 seconds
})

onBeforeUnmount(() => clearInterval?.(checkInterval))
</script>

<style scoped>
/* Custom animations for popup appearance */
.popup-enter-active {
  transition: all 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}

.popup-leave-active {
  transition: all 0.4s cubic-bezier(0.55, 0.085, 0.68, 0.53);
}

.popup-enter-from {
  transform: translateX(100%) scale(0.9);
  opacity: 0;
}

.popup-leave-to {
  transform: translateX(100%) scale(0.9);
  opacity: 0;
}

.popup-move {
  transition: transform 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}
</style>
