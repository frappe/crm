<template>
  <Popover
    class="inline-block"
    :placement="placement"
    @open="initFromValue"
    @close="view = 'date'"
  >
    <template #target="{ togglePopover }">
      <Button
        variant="ghost"
        class="text-lg font-medium text-ink-gray-7"
        :label="__(displayLabel)"
        iconRight="chevron-down"
        @click="togglePopover"
      />
    </template>
    <template #body="{ togglePopover }">
      <div
        class="w-fit min-w-60 select-none text-base text-ink-gray-9 rounded-lg bg-surface-modal shadow-2xl ring-1 ring-black ring-opacity-5 mt-2"
      >
        <!-- Navigation / Label -->
        <div class="flex items-center justify-between p-2 pb-0 gap-1">
          <Button
            variant="ghost"
            size="sm"
            class="text-sm font-medium text-ink-gray-7"
            @click="cycleView"
          >
            <span v-if="view === 'date'">
              {{ __(months[currentMonth]) }} {{ __(currentYear) }}
            </span>
            <span v-else-if="view === 'month'">{{ __(currentYear) }}</span>
            <span v-else>
              {{ __(yearRangeStart) }} - {{ __(yearRangeStart + 11) }}
            </span>
          </Button>
          <div class="flex items-center">
            <Button
              variant="ghost"
              icon="chevron-left"
              class="size-7"
              @click="prev"
            />
            <Button
              variant="ghost"
              class="text-xs"
              :label="__('Today')"
              @click="
                () => {
                  selectDate(dayjs().toDate())
                  togglePopover()
                }
              "
            />
            <Button
              variant="ghost"
              icon="chevron-right"
              class="size-7"
              @click="next"
            />
          </div>
        </div>
        <!-- Views -->
        <div class="p-2">
          <!-- Date grid -->
          <div v-if="view === 'date'">
            <div
              class="flex items-center text-xs font-medium uppercase text-ink-gray-4 mb-1"
            >
              <div
                v-for="d in ['S', 'M', 'T', 'W', 'T', 'F', 'S']"
                :key="d"
                class="flex h-6 w-8 items-center justify-center"
              >
                {{ __(d) }}
              </div>
            </div>
            <div v-for="(week, wi) in weeks" :key="wi" class="flex">
              <div
                v-for="dateObj in week"
                :key="dateObj.key"
                class="flex h-8 w-8 items-center justify-center rounded cursor-pointer text-sm"
                :class="[
                  dateObj.inMonth ? 'text-ink-gray-8' : 'text-ink-gray-3',
                  dateObj.isToday ? 'font-extrabold text-ink-gray-9' : '',
                  dateObj.isSelected
                    ? 'bg-surface-gray-6 text-ink-white hover:bg-surface-gray-6'
                    : 'hover:bg-surface-gray-2',
                ]"
                @click="
                  () => {
                    selectDate(dateObj.date)
                    togglePopover()
                  }
                "
              >
                {{ __(dateObj.date.date()) }}
              </div>
            </div>
          </div>
          <!-- Month grid -->
          <div v-else-if="view === 'month'" class="grid grid-cols-3 gap-1">
            <div
              v-for="(m, i) in months"
              :key="m"
              class="py-2 text-sm rounded cursor-pointer text-center hover:bg-surface-gray-2"
              :class="{
                'bg-surface-gray-6 text-ink-white hover:bg-surface-gray-6':
                  i === currentMonth,
              }"
              @click="selectMonth(i)"
            >
              {{ __(m.slice(0, 3)) }}
            </div>
          </div>
          <!-- Year grid -->
          <div v-else class="grid grid-cols-3 gap-1">
            <div
              v-for="y in yearRange"
              :key="y"
              class="py-2 text-sm rounded cursor-pointer text-center hover:bg-surface-gray-2"
              :class="{
                'bg-surface-gray-6 text-ink-white hover:bg-surface-gray-6':
                  y === currentYear,
              }"
              @click="selectYear(y)"
            >
              {{ __(y) }}
            </div>
          </div>
        </div>
      </div>
    </template>
  </Popover>
</template>
<script setup>
import { ref, computed, watch } from 'vue'
import { Popover, Button, dayjs } from 'frappe-ui'

const props = defineProps({
  modelValue: { type: String, default: '' },
  placement: { type: String, default: 'bottom-start' },
  formatter: { type: Function, default: (d) => dayjs(d).format('MMM, YYYY') },
})
const emit = defineEmits(['update:modelValue'])

const view = ref('date') // 'date' | 'month' | 'year'
const currentYear = ref(dayjs().year())
const currentMonth = ref(dayjs().month()) // 0-index
const selected = ref(props.modelValue || dayjs().format('YYYY-MM-DD'))

function initFromValue() {
  if (props.modelValue) {
    const d = dayjs(props.modelValue)
    if (d.isValid()) {
      currentYear.value = d.year()
      currentMonth.value = d.month()
      selected.value = d.format('YYYY-MM-DD')
    }
  }
}

watch(
  () => props.modelValue,
  (val) => {
    if (val && dayjs(val).isValid()) {
      const d = dayjs(val)
      selected.value = d.format('YYYY-MM-DD')
      currentYear.value = d.year()
      currentMonth.value = d.month()
    }
  },
)

const months = [
  'Jan',
  'Feb',
  'Mar',
  'Apr',
  'May',
  'Jun',
  'Jul',
  'Aug',
  'Sep',
  'Oct',
  'Nov',
  'Dec',
]

const displayLabel = computed(() => props.formatter(selected.value))

function monthStart() {
  return dayjs(`${currentYear.value}-${currentMonth.value + 1}-01`)
}

const weeks = computed(() => {
  const start = monthStart().startOf('week')
  const end = monthStart().endOf('month').endOf('week')
  const days = []
  let d = start
  while (d.isBefore(end) || d.isSame(end)) {
    const inMonth = d.month() === currentMonth.value
    const sel = dayjs(selected.value)
    days.push({
      date: d,
      key: d.format('YYYY-MM-DD'),
      inMonth,
      isToday: d.isSame(dayjs(), 'day'),
      isSelected: sel.isValid() && d.isSame(sel, 'day'),
    })
    d = d.add(1, 'day')
  }
  const chunked = []
  for (let i = 0; i < days.length; i += 7) chunked.push(days.slice(i, i + 7))
  return chunked
})

function selectDate(date) {
  const d = dayjs(date)
  if (!d.isValid()) return
  selected.value = d.format('YYYY-MM-DD')
  emit('update:modelValue', selected.value)
  view.value = 'date'
}
function selectMonth(i) {
  currentMonth.value = i
  view.value = 'date'
}
function selectYear(y) {
  currentYear.value = y
  view.value = 'month'
}
function prev() {
  if (view.value === 'date') {
    const m = monthStart().subtract(1, 'month')
    currentYear.value = m.year()
    currentMonth.value = m.month()
  } else if (view.value === 'month') {
    currentYear.value -= 1
  } else {
    yearRangeStart.value -= 12
  }
}
function next() {
  if (view.value === 'date') {
    const m = monthStart().add(1, 'month')
    currentYear.value = m.year()
    currentMonth.value = m.month()
  } else if (view.value === 'month') {
    currentYear.value += 1
  } else {
    yearRangeStart.value += 12
  }
}
function cycleView() {
  if (view.value === 'date') view.value = 'month'
  else if (view.value === 'month') view.value = 'year'
  else view.value = 'date'
}

const yearRangeStart = ref(currentYear.value - (currentYear.value % 12))
const yearRange = computed(() =>
  Array.from({ length: 12 }, (_, i) => yearRangeStart.value + i),
)
watch(currentYear, (y) => {
  if (y < yearRangeStart.value || y > yearRangeStart.value + 11)
    yearRangeStart.value = y - (y % 12)
})
</script>
