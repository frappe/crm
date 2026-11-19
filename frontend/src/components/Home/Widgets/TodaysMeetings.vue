<template>
  <HomeWidget
    :title="__('Today\'s meetings')"
    subtitle=""
    :resource="resource"
    :emptyText="__('No meetings today.')"
    emptyIcon="lucide-calendar-check"
  >
    <template #subtitle>
      <span class="truncate text-base text-ink-gray-5">
        <template v-if="total">
          <span class="text-base-semibold text-ink-gray-9">{{ total }}</span>
          {{ total === 1 ? __('meeting today') : __('meetings today') }}
        </template>
        <template v-else>{{ __('Nothing on the calendar') }}</template>
      </span>
    </template>
    <template #tabs>
      <Button
        icon="lucide-plus"
        :tooltip="__('New meeting')"
        @click="showNewMeeting = true"
      />
    </template>
    <template #default="{ rows }">
      <div class="flex flex-col gap-1 pb-1">
        <ItemListRow
          v-for="row in rows"
          :key="row.name"
          :as="RouterLink"
          :to="meetingRoute(row)"
          size="lg"
          class="hover:bg-surface-gray-2"
          :class="{ 'opacity-50': hasEnded(row) }"
        >
          <template #prefix>
            <div
              class="h-9 w-1 rounded-full"
              :style="{ backgroundColor: meetingColor(row) }"
            />
          </template>
          <template #label>
            <div class="flex flex-col gap-1">
              <div class="flex items-center gap-1.5 text-sm text-ink-gray-5">
                <template v-if="isOngoing(row)">
                  <Badge size="sm" theme="green" :label="__('Now')" />
                  <span class="truncate">{{ meetingUntil(row) }}</span>
                </template>
                <span v-else class="truncate">{{ meetingTime(row) }}</span>
              </div>
              <div class="truncate text-base-medium text-ink-gray-8">
                {{ row.subject || __('(No title)') }}
              </div>
            </div>
          </template>
          <template #suffix>
            <div class="flex items-center gap-1">
              <Button
                v-if="meetingLink(row) && !hasEnded(row)"
                variant="ghost"
                icon="lucide-video"
                :tooltip="__('Join')"
                :href="meetingLink(row)"
                @click.stop
              />
              <div class="flex -space-x-1.5">
                <Tooltip
                  v-for="person in row.attendees.slice(0, 2)"
                  :key="person.email"
                  :text="person.name || person.email"
                >
                  <Avatar
                    class="ring-2 ring-outline-base"
                    shape="circle"
                    size="md"
                    :image="person.image"
                    :label="person.name || person.email"
                  />
                </Tooltip>
              </div>
              <Tooltip
                v-if="row.attendees.length > 2"
                :text="moreNames(row.attendees)"
              >
                <Badge :label="String(row.attendees.length - 2)" />
              </Tooltip>
            </div>
          </template>
        </ItemListRow>
      </div>
    </template>
    <template #footer>
      <Button
        class="mr-auto"
        variant="ghost"
        :label="__('See calendar')"
        iconRight="lucide-arrow-right"
        :route="{ name: 'Calendar' }"
      />
    </template>
  </HomeWidget>
  <EventModal v-if="showNewMeeting" v-model="showNewMeeting" />
</template>
<script setup lang="ts">
import HomeWidget from '@/components/Home/HomeWidget.vue'
import EventModal from '@/components/Modals/EventModal.vue'
import { refreshHome, useHomeWidget } from '@/composables/homeWidget'
import {
  hasEnded,
  isOngoing,
  meetingLink,
  meetingRoute,
  meetingTime,
  meetingUntil,
} from '@/utils/meetings'
import { Avatar, Badge, Button, ItemListRow, Tooltip } from 'frappe-ui'
import { CalendarColorMap } from 'frappe-ui/experimental'
import { computed, ref, watch } from 'vue'
import { RouterLink } from 'vue-router'

interface Attendee {
  email: string
  name?: string
  image?: string
}

// Declared so Home's `config` does not fall through to HomeWidget and show the doctype setting
defineProps<{ config?: Record<string, unknown> | null }>()

const resource = useHomeWidget('todays_meetings')
const total = computed<number>(() => resource.data?.total || 0)

const showNewMeeting = ref(false)
watch(showNewMeeting, (open) => open || refreshHome())

// Events store a calendar colour name or a CSS colour; the calendar shows none as green.
function meetingColor(meeting: { color?: string | null }): string {
  const color = meeting.color || 'green'
  return CalendarColorMap[color]?.color || color
}

function moreNames(attendees: Attendee[]): string {
  return attendees
    .slice(2)
    .map((person) => person.name || person.email)
    .join(', ')
}
</script>
