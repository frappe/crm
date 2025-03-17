<template>
  <div v-if="events.length">
    <div v-for="(event, i) in events" :key="event.name">
      <div
        class="activity flex cursor-pointer gap-6 rounded p-2.5 duration-300 ease-in-out hover:bg-gray-1"
        @click="modalRef.showEvent(event)"
      >
        <div class="flex flex-1 flex-col gap-1.5 text-base truncate">
          <div class="font-medium text-ink-gray-9 truncate">
            {{ event.subject }}
          </div>
          <div class="flex gap-1.5 text-ink-gray-8">
            <div v-if="event.date" class="flex items-center justify-center">
              <DotIcon class="h-2.5 w-2.5 text-ink-gray-5" :radius="2" />
            </div>
            <div v-if="event.starts_on">
              <Tooltip :text="dateFormat(event.starts_on, 'ddd, MMM D, YYYY | hh:mm a')">
                <div class="flex gap-2">
                  <CalendarIcon />
                  <div>{{ dateFormat(event.starts_on, 'D MMM, hh:mm a') }}</div>
                </div>
              </Tooltip>
            </div>
            <div v-if="event.ends_on">
              <Tooltip :text="dateFormat(event.ends_on, 'ddd, MMM D, YYYY | hh:mm a')">
                <div class="flex gap-2">
                  <CalendarIcon />
                  <div>{{ dateFormat(event.ends_on, 'D MMM, hh:mm a') }}</div>
                </div>
              </Tooltip>
            </div>
            <div class="flex items-center justify-center">
              <DotIcon class="h-2.5 w-2.5 text-ink-gray-5" :radius="2" />
            </div>
          </div>
        </div>
        <div class="flex items-center gap-1">
          <Dropdown :options="eventStatusOptions(modalRef.updateEventStatus, event)" @click.stop>
            <Tooltip :text="__('Change Status')">
              <Button variant="ghosted" class="hover:bg-surface-gray-4">
                <EventStatusIcon :status="event.status" />
              </Button>
            </Tooltip>
          </Dropdown>
          <Dropdown
            :options="[
              {
                label: __('Delete'),
                icon: 'trash-2',
                onClick: () => {
                  $dialog({
                    title: __('Delete Event'),
                    message: __('Are you sure you want to delete this event?'),
                    actions: [
                      {
                        label: __('Delete'),
                        theme: 'red',
                        variant: 'solid',
                        onClick(close) {
                          modalRef.deleteEvent(event.name)
                          close()
                        },
                      },
                    ],
                  })
                },
              },
            ]"
            @click.stop
          >
            <Button icon="more-horizontal" variant="ghosted" class="hover:bg-surface-gray-4 text-ink-gray-9" />
          </Dropdown>
        </div>
      </div>
      <div v-if="i < events.length - 1" class="mx-2 h-px border-t border-gray-200" />
    </div>
  </div>
</template>
<script setup>
import CalendarIcon from '@/components/Icons/CalendarIcon.vue'
import EventStatusIcon from '@/components/Icons/EventStatusIcon.vue'
import DotIcon from '@/components/Icons/DotIcon.vue'
import { dateFormat, eventStatusOptions } from '@/utils'
import { globalStore } from '@/stores/global'
import { Tooltip, Dropdown } from 'frappe-ui'

const props = defineProps({
  events: Array,
  modalRef: Object,
})

const { $dialog } = globalStore()
</script>
