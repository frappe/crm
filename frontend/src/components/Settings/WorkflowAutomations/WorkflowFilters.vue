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
      {{ __('A trigger runs only when every filter matches.') }}
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
  // Trigger filters are evaluated by `evaluate_filters`, which only ANDs a flat list. In that
  // mode groups are hidden (level 3) and an `or` is snapped back, so nothing is stored that
  // the engine would quietly ignore.
  flat: { type: Boolean, default: false },
})

const emit = defineEmits(['update:modelValue'])

const conditions = reactive(parse(props.modelValue))

watch(
  conditions,
  () => {
    if (props.flat) forceAnd(conditions)
    emit('update:modelValue', serialize(conditions))
  },
  { deep: true },
)

function forceAnd(rows) {
  rows.forEach((item, index) => {
    if (item === 'or') rows[index] = 'and'
  })
}

// Selecting another step hands this the next condition, so reload the array in place.
watch(
  () => props.modelValue,
  (value) => {
    if (serialize(conditions) === serialize(parse(value))) return
    conditions.splice(0, conditions.length, ...parse(value))
  },
)

function parse(value) {
  const rows = read(value)
  return props.flat ? interleave(rows) : rows
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

/** A stored flat list carries no conjunctions; the builder expects them between the rows. */
function interleave(rows) {
  return rows.flatMap((row, index) => (index ? ['and', row] : [row]))
}

function serialize(value) {
  const rows = props.flat ? leaves(value) : value
  return rows.length ? JSON.stringify(rows) : ''
}

function leaves(value) {
  return value
    .filter((item) => Array.isArray(item))
    .flatMap((item) => (Array.isArray(item[0]) ? leaves(item) : [item]))
}
</script>
