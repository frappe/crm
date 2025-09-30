<template>
  <Teleport to="body">
    <div
      v-if="visibleAlerts.length > 0"
      class="fixed top-4 right-4 bottom-4 z-50 w-96"
    >
      <TransitionGroup name="popup" tag="div" class="space-y-2">
        <div
          v-for="alert in visibleAlerts"
          :key="alert.id"
          class="bg-surface-gray-6 rounded-lg shadow-2xl"
        >
          <div class="flex justify-between items-center gap-1 p-3">
            <div class="flex items-stretch space-x-2">
              <div
                class="w-[2px] rounded shrink-0"
                :style="{
                  backgroundColor:
                    CalendarColorMapDark[alert.notification.color]?.color ||
                    '#30A66D',
                }"
              />
              <div class="flex flex-col">
                <div
                  class="text-base font-semibold text-ink-white mb-1 hover:text-ink-gray-2 cursor-pointer"
                  @click="openEvent(alert)"
                >
                  {{ alert.notification.subject || 'Event Notification' }}
                </div>
                <div class="text-ink-gray-4 text-sm">
                  {{ formatEventTime(alert.notification) }}
                </div>
              </div>
            </div>

            <div class="flex items-center gap-1">
              <div
                class="flex gap-1 h-fit items-center text-sm text-ink-amber-1 bg-surface-amber-3 rounded-full px-2 py-1"
              >
                <div><LucideZap class="size-3" /></div>
                <div>{{ getTimeUntilEvent(alert.notification) }}</div>
              </div>
              <Button
                class="text-ink-white hover:bg-surface-gray-5 !size-6"
                variant="ghost"
                icon="x"
                @click="completeAlert(alert.id)"
              />
            </div>
          </div>
        </div>
      </TransitionGroup>
    </div>
  </Teleport>
</template>

<script setup>
import { useEventNotificationAlert } from '@/data/notifications'
import { Button, dayjs, CalendarColorMapDark } from 'frappe-ui'
import { computed, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

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

function getTimeUntilEvent(notification) {
  if (notification.starts_on) {
    const eventTime = dayjs(notification.starts_on)
    const now = dayjs()
    const diffMinutes = eventTime.diff(now, 'minute')

    if (diffMinutes <= 0) {
      return __('Starting now')
    } else if (diffMinutes < 60) {
      return __('In {0} minutes', [diffMinutes])
    } else {
      const diffHours = Math.floor(diffMinutes / 60)
      const remainingMinutes = diffMinutes % 60
      if (remainingMinutes === 0) {
        return __('In {0} hour{1}', [diffHours, diffHours > 1 ? 's' : ''])
      } else {
        return __('In {0}h {1}m', [diffHours, remainingMinutes])
      }
    }
  }
  return __('Soon')
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
