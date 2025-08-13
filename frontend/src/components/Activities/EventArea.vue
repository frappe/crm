<template>
  <div class="mb-5">
    <div class="mb-1 flex items-center justify-stretch gap-2 py-1 text-base">
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
            :avatars="[
              {
                image: event.owner.image,
                label: event.owner.label,
                name: event.owner.label,
              },
              {
                image: event.owner.image,
                label: event.owner.label,
                name: event.owner.label,
              },
            ]"
            size="sm"
          />
        </div>
        <div class="flex justify-between gap-2 items-center text-ink-gray-6">
          <div>{{ formattedDateTime }}</div>
          <div>{{ formattedDate }}</div>
        </div>
      </div>
    </div>
  </div>
  <EventModal
    v-if="showEventModal"
    v-model="showEventModal"
    v-model:events="events"
    :event="event"
    :doctype="doctype"
    :docname="docname"
  />
</template>
<script setup>
import EventModal from '@/components/Modals/EventModal.vue'
import MultipleAvatar from '@/components/MultipleAvatar.vue'
import { Tooltip, Avatar, dayjs } from 'frappe-ui'
import { formatDate, timeAgo } from '@/utils'
import { computed, ref } from 'vue'

const props = defineProps({
  event: {
    type: Object,
    required: true,
  },
  doctype: {
    type: String,
    default: '',
  },
  docname: {
    type: String,
    default: '',
  },
})

const events = defineModel()

const formattedDateTime = computed(() => {
  const start = dayjs(props.event.starts_on)
  const end = dayjs(props.event.ends_on)

  if (props.event.all_day) {
    return __('All day')
  }

  return `${start.format('h:mm a')} - ${end.format('h:mm a')}`
})

const formattedDate = computed(() => {
  const start = dayjs(props.event.starts_on)
  return start.format('ddd, D MMM YYYY')
})

const showEventModal = ref(false)

function showEvent() {
  showEventModal.value = true
}
</script>
