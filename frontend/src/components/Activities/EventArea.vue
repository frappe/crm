<template>
  <div v-for="(event, i) in events" :key="event.name">
    <div
      class="activity grid grid-cols-[30px_minmax(auto,_1fr)] gap-4 px-3 sm:px-10"
    >
      <div
        class="z-0 relative flex justify-center before:absolute before:left-[50%] before:-z-[1] before:top-0 before:border-l before:border-outline-gray-modals"
        :class="i != events.length - 1 ? 'before:h-full' : 'before:h-4'"
      >
        <div
          class="flex h-8 w-7 items-center justify-center bg-surface-white text-ink-gray-8"
        >
          <CalendarIcon class="h-4 w-4" />
        </div>
      </div>
      <div class="mb-5">
        <div
          class="mb-1 flex items-center justify-stretch gap-2 py-1 text-base"
        >
          <div class="inline-flex items-center flex-wrap gap-1 text-ink-gray-5">
            <Avatar
              :image="event.owner.image"
              :label="event.owner.label"
              size="md"
            />
            <span class="font-medium text-ink-gray-8 ml-1">
              {{ event.owner.label }}
            </span>
            <span>{{ 'has created an event' }}</span>
          </div>
          <div class="ml-auto whitespace-nowrap">
            <Tooltip :text="formatDate(event.creation)">
              <div class="text-sm text-ink-gray-5">
                {{ __(timeAgo(event.creation)) }}
              </div>
            </Tooltip>
          </div>
        </div>
        <div
          class="flex gap-2 border cursor-pointer border-outline-gray-modals rounded-lg bg-surface-cards px-2.5 py-2.5 text-ink-gray-9"
          @click="showEvent(event)"
        >
          <div
            class="flex w-[2px] rounded-lg"
            :style="{ backgroundColor: event.color || '#30A66D' }"
          />
          <div class="flex-1 flex flex-col gap-1 text-base">
            <div
              class="flex items-center justify-between gap-2 font-medium text-ink-gray-7"
            >
              <div>{{ event.subject }}</div>
              <MultipleAvatar
                v-if="event.participants?.length > 1"
                :avatars="event.participants"
                size="sm"
              />
            </div>
            <div
              class="flex justify-between gap-2 items-center text-ink-gray-6"
            >
              <div>{{ formattedDateTime(event) }}</div>
              <div>{{ formattedDate(event) }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
  <EventModal
    v-if="showEventModal"
    v-model="showEventModal"
    v-model:events="eventsResource"
    :event="event"
    :doctype="doctype"
    :docname="docname"
  />
</template>
<script setup>
import CalendarIcon from '@/components/Icons/CalendarIcon.vue'
import EventModal from '@/components/Modals/EventModal.vue'
import MultipleAvatar from '@/components/MultipleAvatar.vue'
import { usersStore } from '@/stores/users'
import { formatDate, timeAgo } from '@/utils'
import { Tooltip, Avatar, dayjs, createListResource } from 'frappe-ui'
import { computed, ref } from 'vue'

const props = defineProps({
  doctype: {
    type: String,
    default: '',
  },
  docname: {
    type: String,
    default: '',
  },
})

const { getUser } = usersStore()

const eventsResource = createListResource({
  doctype: 'Event',
  cache: ['calendar', props.docname],
  fields: [
    'name',
    'status',
    'subject',
    'description',
    'starts_on',
    'ends_on',
    'all_day',
    'event_type',
    'color',
    'owner',
    'reference_doctype',
    'reference_docname',
    'creation',
  ],
  filters: {
    reference_doctype: props.doctype,
    reference_docname: props.docname,
  },
  auto: true,
  orderBy: 'creation desc',
  onSuccess: (d) => {
    console.log(d)
  },
})

const eventParticipants = createListResource({
  doctype: 'Event Participants',
  cache: ['Event Participants', props.docname],
  fields: ['*'],
  parent: 'Event',
})

const events = computed(() => {
  if (!eventsResource.data) return []

  if (!eventParticipants.data?.length) {
    eventParticipants.update({
      filters: {
        parenttype: 'Event',
        parentfield: 'event_participants',
        parent: ['in', eventsResource.data.map((e) => e.name)],
      },
    })
    !eventParticipants.list.loading && eventParticipants.reload()
  } else {
    eventsResource.data.forEach((event) => {
      if (typeof event.owner !== 'object') {
        event.owner = {
          label: getUser(event.owner).full_name,
          image: getUser(event.owner).user_image,
          name: event.owner,
        }
      }

      event.participants = [
        event.owner,
        ...eventParticipants.data
          .filter((participant) => participant.parent === event.name)
          .map((participant) => ({
            label: getUser(participant.email).full_name || participant.email,
            image: getUser(participant.email).user_image || '',
            name: participant.email,
          })),
      ]
    })
  }

  return eventsResource.data
})

const formattedDateTime = (e) => {
  const start = dayjs(e.starts_on)
  const end = dayjs(e.ends_on)

  if (e.all_day) {
    return __('All day')
  }

  return `${start.format('h:mm a')} - ${end.format('h:mm a')}`
}

const formattedDate = (e) => {
  const start = dayjs(e.starts_on)
  return start.format('ddd, D MMM YYYY')
}

const showEventModal = ref(false)
const event = ref(null)

function showEvent(e) {
  showEventModal.value = true
  event.value = e
}
</script>
