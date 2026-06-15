<template>
  <div class="p-6.5 px-5 rounded-xl border border-outline-gray-2">
    <div class="mb-6.5 flex justify-between items-center">
      <div class="ml-1">
        <Popover v-if="startYear !== endYear">
          <template #target="{ togglePopover }">
            <Button
              class="flex items-center gap-2 font-semibold text-xl cursor-pointer select-none"
              variant="ghost"
              @click="togglePopover"
              :label="currentYear + ''"
              icon-right="chevron-down"
            />
          </template>
          <template #body-main="{ togglePopover }">
            <div class="w-24">
              <div ref="yearsContainer" class="max-h-60 overflow-y-auto">
                <div
                  v-for="year in yearsList"
                  :key="year"
                  ref="yearItems"
                  class="cursor-pointer px-3 py-1.5 text-sm hover:bg-surface-gray-2 flex items-center justify-between text-ink-gray-8 rounded"
                  @click="onYearChange(togglePopover, year)"
                >
                  {{ year }}
                  <FeatherIcon
                    name="check"
                    class="size-4"
                    v-if="year === currentYear"
                  />
                </div>
              </div>
            </div>
          </template>
        </Popover>
        <div
          v-else
          class="flex items-center gap-2 px-2 font-semibold text-xl select-none"
        >
          {{ startYear }}
        </div>
      </div>
      <div class="flex gap-2 items-center">
        <Button
          variant="ghost"
          icon="chevron-left"
          :disabled="visibleMonths === 'first-half'"
          @click="visibleMonths = 'first-half'"
        />
        <Button variant="ghost" label="Today" @click="goToToday()" />
        <Button
          variant="ghost"
          icon="chevron-right"
          :disabled="visibleMonths === 'second-half'"
          @click="visibleMonths = 'second-half'"
        />
      </div>
    </div>
    <div
      class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5"
      v-if="visibleMonths === 'first-half'"
    >
      <HLCalender
        v-for="month in months.slice(0, 6)"
        :key="month"
        :year="currentYear"
        :month="month"
        :holidays="holidayListData.holidays"
      />
    </div>
    <div
      class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 justify-between gap-5"
      v-else
    >
      <HLCalender
        v-for="month in months.slice(6, 12)"
        :key="month"
        :year="currentYear"
        :month="month"
        :holidays="holidayListData.holidays"
      />
    </div>
    <div class="flex gap-2 items-center w-full justify-center mt-8">
      <div
        :class="[
          'size-1.5 rounded-full cursor-pointer',
          {
            'bg-surface-gray-7': visibleMonths === 'first-half',
            'bg-surface-gray-4': visibleMonths === 'second-half',
          },
        ]"
        @click="visibleMonths = 'first-half'"
      />
      <div
        :class="[
          'size-1.5 rounded-full cursor-pointer',
          {
            'bg-surface-gray-7': visibleMonths === 'second-half',
            'bg-surface-gray-4': visibleMonths === 'first-half',
          },
        ]"
        @click="visibleMonths = 'second-half'"
      />
    </div>
  </div>
</template>
<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import dayjs from 'dayjs'
import { Button, Popover } from 'frappe-ui'
import HLCalender from './HLCalender.vue'
import { holidayListData } from './utils'

const visibleMonths = ref('first-half')
const months = ref([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12])
const currentYear = ref(dayjs().year())

const startYear = ref(dayjs(holidayListData.value.from_date || dayjs()).year())
const endYear = ref(dayjs(holidayListData.value.to_date || dayjs()).year())

const yearsList = computed(() => {
  const yearList = []
  for (let year = startYear.value; year <= endYear.value; year++) {
    yearList.push(year)
  }
  return yearList
})

const onYearChange = (togglePopover, year) => {
  currentYear.value = year
  if (
    year === dayjs(holidayListData.value.from_date).year() &&
    dayjs(holidayListData.value.from_date).month() >= 6
  ) {
    visibleMonths.value = 'second-half'
  } else {
    visibleMonths.value = 'first-half'
  }
  togglePopover()
}

const goToToday = () => {
  const today = dayjs()
  currentYear.value = today.year()
  visibleMonths.value = today.month() >= 6 ? 'second-half' : 'first-half'
}

watch(
  () => [holidayListData.value.from_date, holidayListData.value.to_date],
  ([fromDate, toDate]) => {
    fromDate = dayjs(fromDate)
    toDate = dayjs(toDate)
    startYear.value = fromDate.year()
    endYear.value = toDate.year()
    currentYear.value = fromDate.year()
    visibleMonths.value = fromDate.month() >= 6 ? 'second-half' : 'first-half'
  },
)

onMounted(() => {
  const fromDate = dayjs(holidayListData.value.from_date || dayjs())
  visibleMonths.value = fromDate.month() >= 6 ? 'second-half' : 'first-half'
})
</script>
