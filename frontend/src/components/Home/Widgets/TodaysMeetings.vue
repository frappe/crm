<template>
  <HomeWidget
    :title="todayTitle"
    subtitle=""
    :resource="resource"
    :emptyText="__('No calls today.')"
    emptyIcon="lucide-calendar-check"
  >
    <template #subtitle>
      <span class="truncate text-base text-ink-gray-5">
        {{
          total === 1
            ? __('1 call today')
            : total
              ? __('{0} calls today', [total])
              : __('Nothing on the calendar')
        }}
      </span>
    </template>
    <template #tabs>
      <Button
        icon="lucide-plus"
        class="rounded-full"
        :tooltip="__('New call')"
        @click="showNewMeeting = true"
      />
    </template>
    <template #default="{ rows }">
      <div class="flex flex-col pb-2">
        <RouterLink
          v-if="next(rows)"
          :to="meetingRoute(next(rows))"
          class="flex items-center gap-3 rounded p-2 hover:bg-surface-gray-2"
        >
          <div
            class="w-0.5 self-stretch rounded-full"
            :style="{ backgroundColor: meetingColor(next(rows)) }"
          />
          <div class="flex min-w-0 flex-1 flex-col gap-1">
            <div class="flex items-center gap-1">
              <Badge
                v-if="isOngoing(next(rows))"
                size="sm"
                variant="solid"
                theme="violet"
                :label="__('Now')"
              />
              <Badge size="sm" :label="meetingCountdown(next(rows))" />
            </div>
            <div
              class="line-clamp-2 break-words text-base-medium text-ink-gray-8"
            >
              {{ next(rows).subject || __('(No title)') }}
            </div>
            <div class="truncate text-sm text-ink-gray-5">
              {{
                [meetingStart(next(rows)), meetingPlace(next(rows))]
                  .filter(Boolean)
                  .join(', ')
              }}
            </div>
            <div
              v-if="next(rows).attendees.length"
              class="flex items-center -space-x-1 pt-1"
            >
              <Tooltip
                v-for="person in next(rows).attendees.slice(0, 3)"
                :key="person.email"
                :text="person.name || person.email"
              >
                <Avatar
                  class="ring-2 ring-outline-base"
                  shape="circle"
                  size="sm"
                  :image="person.image"
                  :label="person.name || person.email"
                />
              </Tooltip>
              <Tooltip
                v-if="next(rows).attendees.length > 3"
                :text="moreNames(next(rows).attendees, 3)"
              >
                <Badge
                  class="ring-2 ring-outline-base"
                  size="sm"
                  :label="String(next(rows).attendees.length - 3)"
                />
              </Tooltip>
            </div>
          </div>
          <Button
            v-if="meetingLink(next(rows))"
            iconLeft="lucide-video"
            :label="__('Join')"
            :href="meetingLink(next(rows))"
            @click.stop
          />
        </RouterLink>

        <div
          v-if="next(rows) && rest(rows).length"
          class="mx-2 my-1.5 border-t border-outline-gray-2"
        />

        <ItemListRow
          v-for="row in rest(rows)"
          :key="row.name"
          :as="RouterLink"
          :to="meetingRoute(row)"
          size="md"
          class="hover:bg-surface-gray-2"
          :class="{ 'opacity-50': hasEnded(row) }"
        >
          <template #prefix>
            <span
              class="size-2 rounded-full"
              :style="{ backgroundColor: meetingColor(row) }"
            />
          </template>
          <template #label>
            <span class="block truncate">
              {{ row.subject || __('(No title)') }}
            </span>
          </template>
          <template #suffix>
            <span class="text-sm text-ink-gray-5">{{ meetingStart(row) }}</span>
          </template>
        </ItemListRow>
      </div>
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
  meetingCountdown,
  meetingLink,
  meetingPlace,
  meetingRoute,
  meetingStart,
  nextMeeting,
  type Meeting,
} from '@/utils/meetings'
import { Avatar, Badge, Button, dayjs, ItemListRow, Tooltip } from 'frappe-ui'
import { CalendarColorMap } from 'frappe-ui/experimental'
import { computed, ref, watch } from 'vue'
import { RouterLink } from 'vue-router'

interface Attendee {
  email: string
  name?: string
  image?: string
}

type Row = Meeting & { attendees: Attendee[] }

// Declared so Home's `config` does not fall through to HomeWidget and show the doctype setting
defineProps<{ config?: Record<string, unknown> | null }>()

const resource = useHomeWidget('todays_meetings')
const total = computed<number>(() => resource.data?.total || 0)
const todayTitle = computed(
  () => `${__("Today's calls")}: ${dayjs().format('ddd D')}`,
)

const showNewMeeting = ref(false)
watch(showNewMeeting, (open) => open || refreshHome())

function next(rows: Row[]): Row | null {
  return nextMeeting(rows)
}

// What's still to come first; meetings that have ended drop to the end.
function rest(rows: Row[]): Row[] {
  const others = rows.filter((row) => row !== next(rows))
  return [
    ...others.filter((row) => !hasEnded(row)),
    ...others.filter((row) => hasEnded(row)),
  ]
}

// Events store a calendar colour name or a CSS colour; the calendar shows none as green.
function meetingColor(meeting: { color?: string | null }): string {
  const color = meeting.color || 'green'
  return CalendarColorMap[color]?.color || color
}

function moreNames(attendees: Attendee[], shown: number): string {
  return attendees
    .slice(shown)
    .map((person) => person.name || person.email)
    .join(', ')
}
</script>
