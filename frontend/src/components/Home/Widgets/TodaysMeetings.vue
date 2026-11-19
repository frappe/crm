<template>
  <HomeWidget
    :title="todayTitle"
    subtitle=""
    :resource="resource"
    :emptyText="__('No meetings today.')"
    emptyIcon="lucide-calendar-check"
  >
    <template #subtitle>
      <span class="truncate text-base text-ink-gray-5">
        {{
          total === 1
            ? __('1 meeting today')
            : total
              ? __('{0} meetings today', [total])
              : __('Nothing on the calendar')
        }}
      </span>
    </template>
    <template #tabs>
      <Button
        icon="lucide-plus"
        class="rounded-full"
        :tooltip="__('New meeting')"
        @click="showNewMeeting = true"
      />
    </template>
    <template #default="{ rows }">
      <div class="flex flex-col pb-2">
        <RouterLink
          v-if="next(rows)"
          :to="meetingRoute(next(rows))"
          class="flex items-center gap-3 rounded-4 p-2 hover:bg-surface-gray-2"
        >
          <div
            class="w-1 self-stretch rounded-full"
            :style="{ backgroundColor: meetingColor(next(rows)) }"
          />
          <div class="flex min-w-0 flex-1 flex-col gap-1.5">
            <div class="flex items-center gap-1">
              <Badge
                v-if="isOngoing(next(rows))"
                variant="solid"
                theme="violet"
                :label="__('Now')"
              />
              <Badge :label="meetingCountdown(next(rows))" />
            </div>
            <div
              class="line-clamp-2 break-words text-lg-semibold text-ink-gray-9"
            >
              {{ next(rows).subject || __('(No title)') }}
            </div>
            <div class="truncate text-base text-ink-gray-6">
              {{
                [meetingStart(next(rows)), meetingPlace(next(rows))]
                  .filter(Boolean)
                  .join(', ')
              }}
            </div>
            <div
              v-if="next(rows).attendees.length"
              class="flex items-center -space-x-1.5 pt-0.5"
            >
              <Tooltip
                v-for="person in next(rows).attendees.slice(0, 3)"
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
              <Tooltip
                v-if="next(rows).attendees.length > 3"
                :text="moreNames(next(rows).attendees, 3)"
              >
                <span
                  class="flex size-6 items-center justify-center rounded-full bg-surface-gray-3 text-xs-medium text-ink-gray-8 ring-2 ring-outline-base"
                >
                  {{ next(rows).attendees.length - 3 }}
                </span>
              </Tooltip>
            </div>
          </div>
          <Button
            v-if="meetingLink(next(rows))"
            size="md"
            iconLeft="lucide-video"
            :label="__('Join')"
            :href="meetingLink(next(rows))"
            @click.stop
          />
        </RouterLink>

        <div
          v-if="next(rows) && rest(rows).length"
          class="mx-2 my-2 border-t border-outline-gray-2"
        />

        <RouterLink
          v-for="row in rest(rows).slice(0, LIST_LIMIT)"
          :key="row.name"
          :to="meetingRoute(row)"
          class="flex h-8 items-center gap-2.5 rounded px-2 hover:bg-surface-gray-2"
          :class="{ 'opacity-50': hasEnded(row) }"
        >
          <span
            class="size-2 shrink-0 rounded-full"
            :style="{ backgroundColor: meetingColor(row) }"
          />
          <span class="flex-1 truncate text-base-medium text-ink-gray-8">
            {{ row.subject || __('(No title)') }}
          </span>
          <span class="shrink-0 text-sm text-ink-gray-5">
            {{ meetingStart(row) }}
          </span>
        </RouterLink>

        <RouterLink
          v-if="more(rows)"
          :to="{ name: 'Calendar' }"
          class="ml-auto mt-1 flex items-center gap-1.5 rounded px-2 py-1 text-sm text-ink-gray-5 hover:text-ink-gray-8"
        >
          <span class="flex -space-x-0.5">
            <span
              v-for="row in hidden(rows).slice(0, 3)"
              :key="row.name"
              class="size-2 rounded-full ring-1 ring-outline-base"
              :style="{ backgroundColor: meetingColor(row) }"
            />
          </span>
          {{ __('{0} more', [more(rows)]) }}
        </RouterLink>
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
import { Avatar, Badge, Button, dayjs, Tooltip } from 'frappe-ui'
import { CalendarColorMap } from 'frappe-ui/experimental'
import { computed, ref, watch } from 'vue'
import { RouterLink } from 'vue-router'

interface Attendee {
  email: string
  name?: string
  image?: string
}

type Row = Meeting & { attendees: Attendee[] }

// Below the next meeting, the rest of the day; the others sit behind "N more".
const LIST_LIMIT = 4

// Declared so Home's `config` does not fall through to HomeWidget and show the doctype setting
defineProps<{ config?: Record<string, unknown> | null }>()

const resource = useHomeWidget('todays_meetings')
const total = computed<number>(() => resource.data?.total || 0)
const todayTitle = computed(() => dayjs().format('ddd D'))

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

function hidden(rows: Row[]): Row[] {
  return rest(rows).slice(LIST_LIMIT)
}

// Counted from the total, since the server sends only the first rows.
function more(rows: Row[]): number {
  return Math.max(
    0,
    total.value - (next(rows) ? 1 : 0) - rest(rows).slice(0, LIST_LIMIT).length,
  )
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
