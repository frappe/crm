<template>
  <div
    class="grid py-3.5 px-4 items-center"
    style="grid-template-columns: 3fr 1fr"
  >
    <div class="text-ink-gray-7 font-medium">{{ __(data.day) }}</div>
    <div class="flex justify-start">
      <Switch v-model="data.active" @update:model-value="toggleDay" />
    </div>
  </div>
  <hr v-if="!isLast" />
</template>

<script setup>
import { Switch } from 'frappe-ui'
import { inject } from 'vue'

const assignmentRuleData = inject('assignmentRuleData')

const props = defineProps({
  data: {
    type: Object,
    required: true,
  },
  isLast: {
    type: Boolean,
    default: false,
  },
})

const toggleDay = (isActive) => {
  const dayIndex = assignmentRuleData.value.assignmentDays.findIndex(
    (d) => d === props.data.day,
  )

  if (isActive && dayIndex === -1) {
    assignmentRuleData.value.assignmentDays.push(props.data.day)
  } else {
    assignmentRuleData.value.assignmentDays.splice(dayIndex, 1)
  }
}
</script>
