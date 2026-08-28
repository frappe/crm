<template>
  <div class="space-y-2">
    <div class="flex items-center justify-between gap-2">
      <label class="block text-sm text-ink-gray-5">{{ label }}</label>
      <TabButtons v-model="mode" :options="modes" />
    </div>

    <WorkflowFilters
      v-if="mode === 'filters'"
      :model-value="filters"
      :doctype="doctype"
      :label="''"
      @update:model-value="setFilters"
    />
    <FormControl
      v-else
      type="textarea"
      :model-value="modelValue"
      :placeholder="placeholder"
      @update:model-value="$emit('update:modelValue', $event)"
    />

    <p v-if="mode !== 'expression'" class="text-xs text-ink-gray-5">
      {{ __('All filters must match.') }}
    </p>
    <p v-else-if="canUseFilters" class="text-xs text-ink-gray-5">
      {{ __('Python, evaluated against doc, target and context.') }}
    </p>
    <p v-else class="text-xs text-ink-gray-5">
      {{ __('Not something filters can express. Edit it below.') }}
    </p>
  </div>
</template>

<script setup>
import { filterableFields } from '@/components/ConditionsFilter/filterableFields'
import WorkflowFilters from './WorkflowFilters.vue'
import {
  isFilterExpression,
  toExpression,
  toFilters,
} from './workflowConditions'
import { FormControl, TabButtons } from 'frappe-ui'
import { computed, ref, watch } from 'vue'

const props = defineProps({
  modelValue: { type: String, default: '' },
  doctype: { type: String, default: '' },
  label: { type: String, default: () => __('Condition') },
  placeholder: { type: String, default: '' },
})

const emit = defineEmits(['update:modelValue'])

const modes = computed(() => [
  { label: __('Filters'), value: 'filters', disabled: !canUseFilters.value },
  { label: __('Expression'), value: 'expression' },
])

/** Start on whichever mode can actually show what is stored. */
const mode = ref(
  isFilterExpression(props.modelValue) ? 'filters' : 'expression',
)

const canUseFilters = computed(() => isFilterExpression(props.modelValue))
const filters = computed(() => toFilters(props.modelValue) || [])

// Selecting another step, or hand-editing past what filters can express, re-picks the mode.
watch(
  () => props.modelValue,
  () => {
    if (!canUseFilters.value) mode.value = 'expression'
  },
)

function setFilters(value) {
  const rows = typeof value === 'string' ? JSON.parse(value || '[]') : value
  // The builder already loaded this DocType's fields; they decide which values stay unquoted.
  emit('update:modelValue', toExpression(rows, filterableFields.data || []))
}
</script>
