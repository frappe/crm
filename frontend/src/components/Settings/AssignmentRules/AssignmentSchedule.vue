<template>
  <div class="rounded-md border px-2 border-outline-gray-2 text-sm">
    <div
      class="grid p-2 px-4 items-center"
      style="grid-template-columns: 3fr 1fr"
    >
      <div
        v-for="column in columns"
        :key="column.key"
        class="text-gray-600 overflow-hidden whitespace-nowrap text-ellipsis"
      >
        {{ __(column.label) }}
      </div>
    </div>
    <hr />
    <AssignmentScheduleItem
      v-for="(day, index) in days"
      :key="day.day"
      :data="day"
      :isLast="index === days.length - 1"
    />
  </div>
  <ErrorMessage :message="assignmentRuleErrors.assignmentDays" class="mt-2" />
</template>

<script setup>
import AssignmentScheduleItem from './AssignmentScheduleItem.vue'
import { ErrorMessage } from 'frappe-ui'
import { onMounted, ref, inject } from 'vue'

const assignmentRuleData = inject('assignmentRuleData')
const assignmentRuleErrors = inject('assignmentRuleErrors')

const columns = [
  {
    label: 'Days',
    key: 'day',
  },
  {
    label: 'Active',
    key: 'active',
  },
]

const days = ref([
  {
    day: 'Monday',
    active: false,
  },
  {
    day: 'Tuesday',
    active: false,
  },
  {
    day: 'Wednesday',
    active: false,
  },
  {
    day: 'Thursday',
    active: false,
  },
  {
    day: 'Friday',
    active: false,
  },
  {
    day: 'Saturday',
    active: false,
  },
  {
    day: 'Sunday',
    active: false,
  },
])

onMounted(() => {
  assignmentRuleData.value.assignmentDays.forEach((day) => {
    const workDay = days.value.find((d) => d.day === day)
    if (workDay) {
      workDay.active = true
    }
  })
})
</script>
