<template>
  <div v-if="show" class="w-[352px] border-l">
    <div
      class="flex items-center justify-between p-4.5 text-ink-gray-7 text-lg font-medium"
    >
      <div>{{ __('Event details') }}</div>
      <div class="flex items-center gap-x-2">
        <Button variant="ghost" @click="editDetails">
          <template #icon>
            <EditIcon class="size-4" />
          </template>
        </Button>
        <Dropdown
          v-if="event.id"
          :options="[
            {
              label: __('Delete'),
              value: 'delete',
              icon: 'trash-2',
              onClick: deleteEvent,
            },
          ]"
        >
          <Button variant="ghost" icon="more-horizontal" />
        </Dropdown>
        <Button
          icon="x"
          variant="ghost"
          @click="
            () => {
              show = false
              activeEvent = ''
            }
          "
        />
      </div>
    </div>
    <div class="text-base">
      <div class="flex items-start gap-2 px-4.5 py-3 pb-0">
        <div
          class="mx-0.5 my-[5px] size-2.5 rounded-full cursor-pointer"
          :style="{
            backgroundColor: event.color || '#30A66D',
          }"
        />
        <div class="flex flex-col gap-[3px]">
          <div class="text-ink-gray-8 font-semibold text-xl">
            {{ event.title || __('(No title)') }}
          </div>
          <div class="text-ink-gray-6 text-p-base">{{ formattedDateTime }}</div>
        </div>
      </div>
      <div class="mx-4.5 my-2.5 border-t border-outline-gray-1" />
      <div>
        <div class="flex gap-2 items-center text-ink-gray-7 px-4.5 py-2">
          <DescriptionIcon class="size-4" />
          {{ __('Description') }}
        </div>
        <div class="px-4.5 py-2 text-ink-gray-7 text-p-base">
          <div
            v-if="event.description && event.description !== '<p></p>'"
            v-html="event.description"
          />
          <div class="text-ink-gray-5" v-else>{{ __('(No description)') }}</div>
        </div>
      </div>
    </div>
  </div>
</template>
<script setup>
import DescriptionIcon from '@/components/Icons/DescriptionIcon.vue'
import EditIcon from '@/components/Icons/EditIcon.vue'
import { Dropdown, CalendarActiveEvent as activeEvent, dayjs } from 'frappe-ui'
import { computed } from 'vue'

const props = defineProps({
  event: {
    type: Object,
    required: true,
  },
})

const show = defineModel()

const emit = defineEmits(['edit', 'delete'])

const formattedDateTime = computed(() => {
  if (props.event.isFullDay) {
    return `${__('All day')} - ${dayjs(props.event.fromDateTime).format('ddd, D MMM YYYY')}`
  }

  const start = dayjs(props.event.fromDateTime)
  const end = dayjs(props.event.toDateTime)
  return `${start.format('h:mm a')} - ${end.format('h:mm a')} ${start.format('ddd, D MMM YYYY')}`
})

function deleteEvent() {
  emit('delete', props.event.id)
}

function editDetails() {
  emit('edit', props.event)
}
</script>
