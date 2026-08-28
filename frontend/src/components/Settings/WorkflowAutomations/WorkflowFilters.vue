<template>
  <div class="space-y-2">
    <label v-if="label" class="block text-sm text-ink-gray-5">{{
      label
    }}</label>
    <CFConditions
      :key="doctype"
      :conditions="conditions"
      :doctype="doctype"
      :is-child="true"
      :level="flat ? 3 : level"
    />
    <p v-if="flat && conditions.length > 1" class="text-xs text-ink-gray-5">
      {{ __('A trigger runs only when these filters match.') }}
    </p>
  </div>
</template>

<script setup>
import CFConditions from '@/components/ConditionsFilter/CFConditions.vue'
import { reactive, watch } from 'vue'

/**
 * The list view's condition builder, reused as-is: it already resolves the DocType's real
 * fields and picks a control per fieldtype, so a value is chosen rather than typed.
 *
 * It edits its `conditions` array in place instead of emitting, so this keeps one reactive
 * array and mirrors it out as JSON whenever it changes.
 */
const props = defineProps({
  modelValue: { type: [String, Array], default: '' },
  doctype: { type: String, default: '' },
  label: { type: String, default: () => __('Filters') },
  level: { type: Number, default: 0 },
  // Hides the grouping controls (level 3). Conjunctions are still stored and honoured.
  flat: { type: Boolean, default: false },
})

const emit = defineEmits(['update:modelValue'])

const conditions = reactive(parse(props.modelValue))

watch(conditions, () => emit('update:modelValue', serialize(conditions)), {
  deep: true,
})

// Selecting another step hands this the next condition, so reload the array in place.
watch(
  () => props.modelValue,
  (value) => {
    if (serialize(conditions) === serialize(parse(value))) return
    conditions.splice(0, conditions.length, ...parse(value))
  },
)

function parse(value) {
  return interleave(read(value))
}

function read(value) {
  if (Array.isArray(value)) return value
  try {
    const parsed = JSON.parse(value || '[]')
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return []
  }
}

/** A list stored without conjunctions means "all of these"; the builder wants them explicit. */
function interleave(rows) {
  if (rows.some((row) => typeof row === 'string')) return rows
  return rows.flatMap((row, index) => (index ? ['and', row] : [row]))
}

function serialize(value) {
  return JSON.stringify(value)
}
</script>
