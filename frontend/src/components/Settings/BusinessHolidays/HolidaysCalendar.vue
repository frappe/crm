<template>
  <div class="p-6 px-5 rounded-7 border border-outline-gray-2">
    <div class="mb-6 flex justify-between items-center">
      <Dropdown v-if="years.length > 1" :options="yearOptions">
        <Button
          variant="ghost"
          class="text-xl-semibold"
          :label="String(currentYear)"
          icon-right="lucide-chevron-down"
        />
      </Dropdown>
      <div v-else class="px-2 text-xl-semibold text-ink-gray-8 select-none">
        {{ currentYear }}
      </div>
      <div class="flex gap-2 items-center">
        <Button
          variant="ghost"
          icon="lucide-chevron-left"
          :aria-label="__('Previous months')"
          :disabled="!canGoBack"
          @click="step(-1)"
        />
        <Button variant="ghost" :label="__('Today')" @click="show('')" />
        <Button
          variant="ghost"
          icon="lucide-chevron-right"
          :aria-label="__('Next months')"
          :disabled="!canGoForward"
          @click="step(1)"
        />
      </div>
    </div>
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
      <MonthCalendar
        v-for="month in visibleMonths"
        :key="`${currentYear}-${month}`"
        :year="currentYear"
        :month="month"
        :holidays-by-date="holidaysByDate"
        :from-date="holidayData.from_date"
        :to-date="holidayData.to_date"
        @add="(date: string) => emit('add', date)"
        @edit="(holiday: Holiday) => emit('edit', holiday)"
      />
    </div>
    <div class="flex gap-2 items-center w-full justify-center mt-8">
      <button
        v-for="half in [0, 1] as const"
        :key="half"
        class="size-1.5 rounded-full"
        :class="
          currentHalf === half ? 'bg-surface-gray-7' : 'bg-surface-gray-4'
        "
        :aria-label="half ? __('July to December') : __('January to June')"
        @click="currentHalf = half"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { Button, dayjs, Dropdown } from 'frappe-ui'
import { computed, ref, watch } from 'vue'
import MonthCalendar from './MonthCalendar.vue'
import { holidayData } from './store'
import type { Holiday } from './types'

const emit = defineEmits<{
  add: [date: string]
  edit: [holiday: Holiday]
}>()

const currentYear = ref(dayjs().year())
// 0 shows January to June, 1 July to December.
const currentHalf = ref<0 | 1>(0)

const startYear = computed(() =>
  dayjs(holidayData.value.from_date || undefined).year(),
)
const endYear = computed(() =>
  Math.max(
    dayjs(holidayData.value.to_date || undefined).year(),
    startYear.value,
  ),
)

const years = computed(() =>
  Array.from(
    { length: endYear.value - startYear.value + 1 },
    (_, i) => startYear.value + i,
  ),
)

const yearOptions = computed(() =>
  years.value.map((year) => ({
    label: String(year),
    onClick: () => (currentYear.value = year),
  })),
)

const visibleMonths = computed(() =>
  Array.from({ length: 6 }, (_, i) => currentHalf.value * 6 + i),
)

const holidaysByDate = computed(
  () =>
    new Map(
      holidayData.value.holidays.map((holiday) => [holiday.date, holiday]),
    ),
)

const canGoBack = computed(
  () => currentYear.value > startYear.value || currentHalf.value === 1,
)
const canGoForward = computed(
  () => currentYear.value < endYear.value || currentHalf.value === 0,
)

// Moves half a year at a time, crossing into the next or previous year.
function step(direction: 1 | -1) {
  const position = currentYear.value * 2 + currentHalf.value + direction
  currentYear.value = Math.floor(position / 2)
  currentHalf.value = (position % 2) as 0 | 1
}

// Shows the half year holding the date, today when it is empty.
function show(date: string) {
  const day = dayjs(date || undefined)
  currentYear.value = day.year()
  currentHalf.value = day.month() >= 6 ? 1 : 0
}

watch(() => holidayData.value.from_date, show, { immediate: true })
</script>
