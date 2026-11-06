<template>
  <div class="w-max mx-auto">
    <div class="text-base-medium mb-2 text-ink-gray-8 ml-2.5">
      {{ monthLabel }}
    </div>
    <div class="text-sm">
      <div class="flex items-center text-xs uppercase">
        <div
          v-for="(day, i) in weekdayLabels"
          :key="i"
          class="flex size-7.5 items-center justify-center text-ink-gray-5"
        >
          {{ day }}
        </div>
      </div>
      <div v-for="(week, i) in weeks" :key="i" class="flex items-center">
        <template v-for="(date, j) in week" :key="date ?? `${i}-${j}`">
          <div v-if="!date" class="size-7.5" />
          <Tooltip
            v-else-if="holidaysByDate.get(date)"
            :text="holidayTooltip(holidaysByDate.get(date) as Holiday)"
            :hover-delay="300"
          >
            <button
              class="flex size-7 m-[1px] items-center justify-center rounded-4 select-none"
              :class="
                holidaysByDate.get(date)?.weekly_off
                  ? 'bg-surface-gray-3 text-ink-gray-6 cursor-default'
                  : 'bg-surface-amber-2 text-ink-amber-7 hover:bg-surface-amber-3'
              "
              :data-date="date"
              @click="onHolidayClick(holidaysByDate.get(date) as Holiday)"
            >
              {{ dayOfMonth(date) }}
            </button>
          </Tooltip>
          <button
            v-else
            class="flex size-7 m-[1px] items-center justify-center rounded-4 select-none"
            :class="
              isInRange(date)
                ? 'text-ink-gray-8 hover:bg-surface-gray-2'
                : 'text-ink-gray-3 cursor-not-allowed'
            "
            :disabled="!isInRange(date)"
            :data-date="date"
            @click="emit('add', date)"
          >
            <span :class="{ 'underline underline-offset-4': date === today }">
              {{ dayOfMonth(date) }}
            </span>
          </button>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { dayjs, Tooltip } from 'frappe-ui'
import { computed } from 'vue'
import type { Holiday } from './types'
import { DATE_FORMAT, getMonthWeeks } from './utils'

const props = defineProps<{
  year: number
  // 0 for January.
  month: number
  holidaysByDate: Map<string, Holiday>
  fromDate: string
  toDate: string
}>()

const emit = defineEmits<{
  add: [date: string]
  edit: [holiday: Holiday]
}>()

const today = dayjs().format(DATE_FORMAT)

const weeks = computed(() => getMonthWeeks(props.year, props.month))

const monthLabel = computed(() =>
  dayjs(new Date(props.year, props.month, 1)).format('MMMM'),
)

// Sunday first, matching getMonthWeeks.
const weekdayLabels = Array.from({ length: 7 }, (_, i) =>
  dayjs().day(i).format('dd').charAt(0),
)

function dayOfMonth(date: string) {
  return Number(date.slice(8))
}

function isInRange(date: string) {
  return (
    Boolean(props.fromDate && props.toDate) &&
    date >= props.fromDate &&
    date <= props.toDate
  )
}

function holidayTooltip(holiday: Holiday) {
  return holiday.weekly_off
    ? __('{0} (weekly off)', [holiday.description])
    : holiday.description
}

// Weekly offs come from the recurring rules, so they are edited there.
function onHolidayClick(holiday: Holiday) {
  if (!holiday.weekly_off) emit('edit', holiday)
}
</script>
