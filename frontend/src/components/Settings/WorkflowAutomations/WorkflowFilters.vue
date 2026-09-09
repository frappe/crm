<template>
  <div class="space-y-2">
    <ConditionBuilder
      :key="doctype"
      :model-value="tree"
      :doctype="doctype"
      :label="label || undefined"
      :max-depth="flat ? 0 : 2"
      bordered="none"
      @update:model-value="store"
    />
    <p
      v-if="flat && tree.conditions.length > 1"
      class="text-xs text-ink-gray-5"
    >
      {{ __('A trigger runs only when these filters match.') }}
    </p>
  </div>
</template>

<script setup>
import {
  ConditionBuilder,
  fromFrappeConditions,
  toFrappeConditions,
} from '@framework/ui/components/ConditionBuilder'
import { computed } from 'vue'

/**
 * The framework's condition builder, bound to the interleaved array the flow stores:
 * leaf rows `[field, operator, value]` with "and" / "or" between them, and a nested
 * list wherever rows were grouped.
 */
const props = defineProps({
  modelValue: { type: [String, Array], default: '' },
  doctype: { type: String, default: '' },
  label: { type: String, default: () => __('Filters') },
  // Hides the grouping controls. Conjunctions are still stored and honoured.
  flat: { type: Boolean, default: false },
})

const emit = defineEmits(['update:modelValue'])

const tree = computed(() => fromFrappeConditions(read(props.modelValue)))

function read(value) {
  if (Array.isArray(value)) return value
  try {
    const parsed = JSON.parse(value || '[]')
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return []
  }
}

function store(next) {
  emit('update:modelValue', JSON.stringify(toFrappeConditions(next).map(row)))
}

/** The builder names its operators; frappe's filter grammar wants its own tokens. */
const TOKENS = { equals: '=', 'not equals': '!=' }

function row(entry) {
  if (typeof entry === 'string') return entry
  if (Array.isArray(entry[0])) return entry.map(row)
  const [fieldname, operator, value] = entry
  // "is not set" is "is" read the other way round, and "is" is all frappe knows.
  if (operator === 'is not')
    return [fieldname, 'is', value === 'set' ? 'not set' : 'set']
  return [fieldname, TOKENS[operator] || operator, value]
}
</script>
