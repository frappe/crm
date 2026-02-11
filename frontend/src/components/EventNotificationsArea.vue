<template>
  <div v-if="events?.length" class="flex flex-col w-full overflow-y-auto">
    <template v-for="(event, i) in computedEvents" :key="event.type">
      <div v-if="event.count" class="p-3">
        <CollapsibleSection :opened="!event.collapsed">
          <template #header="{ opened, toggle }">
            <div class="flex items-center justify-between">
              <div
                class="flex text-ink-gray-6 max-w-fit cursor-pointer items-center gap-2 text-base"
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
                <Badge :label="event.count" variant="ghost" size="sm" />
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
                  class="flex flex-col justify-center items-center shadow bg-surface-white size-8 rounded-[8px]"
                >
                  <div
                    class="uppercase text-[8px] font-semibold text-ink-red-4"
                  >
                    {{ eventDate(e).month }}
                  </div>
                  <div class="text-base font-semibold -mt-0.5">
                    {{ eventDate(e).day }}
                  </div>
                </div>
                <div class="flex flex-col gap-0.5 text-base truncate">
                  <div class="flex items-center gap-1">
                    <div class="flex justify-center items-center size-4">
                      <div
                        class="size-[6px] rounded shrink-0"
                        :style="{ backgroundColor: e.color || '#30A66D' }"
                      />
                    </div>
                    <div class="font-medium text-ink-gray-7">{{ e.title }}</div>
                  </div>
                  <div class="text-ink-gray-6 ml-1">
                    {{ formattedDateTime(e) }}
                  </div>
                </div>
              </div>

              <div class="flex items-center gap-2 flex-shrink-0">
                <MultipleAvatar
                  v-if="e.participants?.length > 1"
                  :avatars="e.participants"
                  size="sm"
                />
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
import MultipleAvatar from '@/components/MultipleAvatar.vue'
import EventIcon from '@/components/Icons/EventIcon.vue'
import { useEventNotifications } from '@/data/notifications'
import { notificationsStore } from '@/stores/notifications'
import { dayjs } from 'frappe-ui'
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
  if (!events.value?.length) return []

  let mappedEvents = events.value.map((event) => {
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
    // Ongoing: Event is currently happening (now is between starts_on + 5 min and ends_on)
    else if (
      dayjs(event.starts_on).isBefore(dayjs().add(5, 'minute')) &&
      dayjs(event.ends_on).isAfter(dayjs())
    ) {
      type = 'ongoing'
    }

    return {
      id: event.name,
      title: event.subject,
      fromDate: dayjs(event.starts_on).format('YYYY-MM-DD'),
      fromTime: dayjs(event.starts_on).format('h:mm a'),
      toTime: dayjs(event.ends_on).format('h:mm a'),
      color: event.color,
      allDay: event.all_day,
      owner: event.owner,
      participants: event.participants,
      type,
    }
  })

  const ongoingEvents = mappedEvents.filter((event) => event.type === 'ongoing')

  const startingNowEvents = mappedEvents.filter(
    (event) => event.type === 'startingNow',
  )

  const upcomingEvents = mappedEvents.filter(
    (event) => event.type === 'upcoming',
  )

  return [
    {
      type: 'Starting now',
      collapsed: false,
      count: startingNowEvents.length,
      items: startingNowEvents,
    },
    {
      type: 'Ongoing events',
      collapsed: false,
      count: ongoingEvents.length,
      items: ongoingEvents,
    },
    {
      type: 'Upcoming events',
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

function eventDate(e) {
  // return date and Month abbreviation return { month: 'Jun', day: '5' }

  const dateObj = dayjs(e.fromDate)
  return {
    day: dateObj.format('DD'),
    month: dateObj.format('MMM'),
  }
}
</script>
