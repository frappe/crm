<template>
  <div class="space-y-2">
    <div class="flex items-start gap-2">
      <Badge :label="kicker" theme="gray" variant="subtle" />
      <div class="min-w-0">
        <div class="text-base-medium text-ink-gray-8">{{ headline }}</div>
        <div
          v-if="detail"
          class="break-words font-mono text-xs text-ink-gray-5"
        >
          {{ detail }}
        </div>
      </div>
    </div>
    <div
      v-if="step.step_type === 'If'"
      class="ml-3 space-y-2 border-l border-outline-gray-2 pl-3"
    >
      <div v-for="arm in arms" :key="arm.name" class="space-y-2">
        <div class="text-xs-semibold text-ink-gray-5">{{ arm.label }}</div>
        <div v-if="!arm.steps.length" class="text-xs text-ink-gray-5">
          {{ __('Nothing here') }}
        </div>
        <WorkflowStepSummary
          v-for="child in arm.steps"
          :key="child._id"
          :step="child"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { Badge } from 'frappe-ui'
import { computed } from 'vue'

const props = defineProps({
  step: { type: Object, required: true },
})

const params = computed(() => {
  try {
    return JSON.parse(props.step.params || '{}')
  } catch {
    return {}
  }
})

const arms = computed(() => [
  { name: 'If', label: __('If'), steps: props.step.children?.If || [] },
  { name: 'Else', label: __('Else'), steps: props.step.children?.Else || [] },
])

const kicker = computed(() => props.step.step_key || props.step.step_type)

const headline = computed(() => {
  if (props.step.step_type === 'If') return __('Condition')
  if (props.step.step_type === 'Wait') {
    return __('Wait {0} {1}', [params.value.value, params.value.unit])
  }
  if (props.step.step_type === 'WaitForEvent') {
    return __('Wait for {0}', [params.value.event_name])
  }
  const target =
    props.step.target && props.step.target !== 'trigger'
      ? ` → ${props.step.target}`
      : ''
  return `${props.step.action_type || __('Action')}${target}`
})

const detail = computed(() => {
  if (props.step.step_type === 'If') return props.step.step_condition
  if (props.step.step_type === 'WaitForEvent') {
    return __('key {0}, timeout {1} {2}', [
      params.value.correlation_key,
      params.value.timeout_value,
      params.value.timeout_unit,
    ])
  }
  const entries = Object.entries(params.value)
  return entries.length
    ? entries.map(([key, value]) => `${key}: ${format(value)}`).join(', ')
    : ''
})

function format(value) {
  return typeof value === 'object' ? JSON.stringify(value) : String(value)
}
</script>
