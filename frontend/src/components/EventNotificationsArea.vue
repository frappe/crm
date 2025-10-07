<template>
  <div v-if="events.data?.length" class="flex flex-col w-full overflow-y-auto">
    <template v-for="(event, i) in computedEvents" :key="event.type">
      <div v-if="event.count" class="p-3">
        <CollapsibleSection :opened="!event.collapsed">
          <template #header="{ opened, toggle }">
            <div class="flex items-center justify-between">
              <div
                class="flex text-ink-gray-9 max-w-fit cursor-pointer items-center gap-2 text-base"
                @click="toggle()"
              >
                <FeatherIcon
                  name="chevron-right"
                  class="h-4 transition-all duration-300 ease-in-out"
                  :class="{ 'rotate-90': opened }"
                />
                <span>
                  {{ __(event.type) }}
                </span>
                <Badge
                  :label="event.count"
                  :theme="
                    event.type === 'Ongoing'
                      ? 'green'
                      : event.type === 'Starting Now'
                        ? 'orange'
                        : 'blue'
                  "
                />
              </div>
            </div>
          </template>

          <div class="flex flex-col space-y-1 mt-2">
            <div
              v-for="e in event.items"
              :key="e.id"
              class="flex items-center justify-between gap-2 h-full p-2 group hover:bg-surface-gray-1 rounded cursor-pointer"
              @click="handleEventClick(e)"
            >
              <div class="flex items-stretch gap-1.5 flex-1 min-w-0">
                <div
                  class="w-[2px] rounded shrink-0"
                  :style="{ backgroundColor: e.color || '#30A66D' }"
                />
                <div
                  class="flex flex-col gap-0.5 text-ink-gray-8 text-base truncate"
                >
                  <div>{{ e.title }}</div>
                  <div class="text-xs text-ink-gray-5">
                    {{ formattedDateTime(e) }}
                  </div>
                </div>
              </div>

              <div class="flex items-center gap-2 flex-shrink-0">
                <span
                  class="text-sm min-w-[50px] text-right"
                  :class="
                    event.type === 'Ongoing'
                      ? 'text-ink-green-3'
                      : event.type === 'Starting Now'
                        ? 'text-ink-amber-3'
                        : 'text-ink-gray-5'
                  "
                >
                  {{ e.date }}
                </span>
              </div>
            </div>
          </div>
        </CollapsibleSection>
      </div>
      <div
        v-if="i < computedEvents.length - 1 && event.count"
        class="border-t border-outline-gray-modals"
      />
    </template>
  </div>

  <div
    v-else
    class="flex flex-1 flex-col items-center justify-center gap-2 p-4"
  >
    <EventIcon class="h-16 w-16 text-ink-gray-3" />
    <div class="text-base font-medium text-ink-gray-3 text-center">
      {{ __('No upcoming events') }}
    </div>
  </div>
</template>
<script setup>
import EventIcon from '@/components/Icons/EventIcon.vue'
import { useEventNotifications } from '@/data/notifications'
import { notificationsStore } from '@/stores/notifications'
import { computed } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const { events } = useEventNotifications()
const { toggle } = notificationsStore()

function handleEventClick(e) {
  toggle()

  router.push({
    name: 'Calendar',
    query: {
      eventId: e.id,
      date: e.fromDate,
    },
  })
}

const computedEvents = computed(() => {
  if (!events.data?.length) return []

  const ongoingEvents = events.data.filter((event) => event.type === 'ongoing')

  const startingNowEvents = events.data.filter(
    (event) => event.type === 'startingNow',
  )

  const upcomingEvents = events.data.filter(
    (event) => event.type === 'upcoming',
  )

  return [
    {
      type: 'Starting Now',
      collapsed: false,
      count: startingNowEvents.length,
      items: startingNowEvents,
    },
    {
      type: 'Ongoing',
      collapsed: false,
      count: ongoingEvents.length,
      items: ongoingEvents,
    },
    {
      type: 'Upcoming',
      collapsed: false,
      count: upcomingEvents.length,
      items: upcomingEvents,
    },
  ]
})

const formattedDateTime = (e) => {
  if (e.allDay) return __('All day')

  if (e.fromTime.includes(':00')) {
    e.fromTime = e.fromTime.replace(':00', '')
  }
  if (e.toTime.includes(':00')) {
    e.toTime = e.toTime.replace(':00', '')
  }

  if (
    (e.fromTime.includes('am') && e.toTime.includes('am')) ||
    (e.fromTime.includes('pm') && e.toTime.includes('pm'))
  ) {
    const fromTime = e.fromTime.replace(' am', '').replace(' pm', '')
    return `${fromTime} - ${e.toTime} `
  }

  return `${e.fromTime} - ${e.toTime}`
}
</script>
