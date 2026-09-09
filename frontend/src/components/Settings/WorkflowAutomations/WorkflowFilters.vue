<template>
  <div class="space-y-2">
    <label v-if="label" class="block text-sm text-ink-gray-5">{{
      label
    }}</label>
    <ConditionBuilder
      v-if="tree.conditions.length"
      :key="doctype"
      :model-value="tree"
      :doctype="doctype"
      :max-depth="flat ? 0 : 2"
      bordered="root"
      @update:model-value="store"
    />
    <!-- The builder's empty state is a box of its own; this is the card every other
         condition builder in the app shows while it holds nothing. -->
    <div v-else class="flex w-full rounded-lg border border-outline-gray-2 p-3">
      <Dropdown v-if="!flat" v-slot="{ open }" :options="addOptions">
        <Button
          :label="__('Add Condition')"
          icon-left="lucide-plus"
          :icon-right="open ? 'lucide-chevron-up' : 'lucide-chevron-down'"
        />
      </Dropdown>
      <Button
        v-else
        :label="__('Add Condition')"
        icon-left="lucide-plus"
        @click="addCondition"
      />
    </div>
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
  emptyTree,
  fromFrappeConditions,
  toFrappeConditions,
} from '@framework/ui/components/ConditionBuilder'
import { Button, Dropdown } from 'frappe-ui'
import { ref, watch } from 'vue'

/** The builder names its operators; frappe's filter grammar wants its own tokens. */
const TOKENS = { equals: '=', 'not equals': '!=' }

/**
 * The framework's condition builder, bound to the interleaved array the flow stores:
 * leaf rows `[field, operator, value]` with "and" / "or" between them, and a nested
 * list wherever rows were grouped.
 *
 * The tree lives here rather than in the stored value: a row with no field yet is
 * dropped on write, so a blank row read back from the store would vanish as it was added.
 */
const props = defineProps({
  modelValue: { type: [String, Array], default: '' },
  doctype: { type: String, default: '' },
  label: { type: String, default: () => __('Filters') },
  // Hides the grouping controls. Conjunctions are still stored and honoured.
  flat: { type: Boolean, default: false },
})

const emit = defineEmits(['update:modelValue'])

const tree = ref(fromFrappeConditions(read(props.modelValue)))

/** What this last mirrored out, so an echo of it doesn't reload the tree. */
let mirrored = serialize(tree.value)

const addOptions = [
  { label: __('Add Condition'), onClick: () => addCondition() },
  { label: __('Add Condition Group'), onClick: () => addGroup() },
]

// Selecting another step hands this the next condition, so reload the tree.
watch(
  () => props.modelValue,
  (value) => {
    const incoming = JSON.stringify(read(value))
    if (incoming === mirrored) return
    tree.value = fromFrappeConditions(read(value))
    mirrored = incoming
  },
)

function addCondition() {
  append({ fieldname: '', operator: 'equals', value: '' })
}

function addGroup() {
  append(emptyTree())
}

function append(node) {
  store({ ...tree.value, conditions: [...tree.value.conditions, node] })
}

function store(next) {
  tree.value = next
  mirrored = serialize(next)
  emit('update:modelValue', mirrored)
}

function serialize(next) {
  return JSON.stringify(toFrappeConditions(next).map(row))
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

<style scoped>
/* The panel is a ~310px column. The app's other condition builders stack a row at
   this width rather than squeezing three controls into it, so this one does too. */
:deep([data-slot='condition-builder']) {
  container-type: inline-size;
}

@container (max-width: 420px) {
  /* Both grids are set inline, on the row and on the leaf's subgrid. */
  :deep([data-slot='condition-group'] li) {
    position: relative;
    grid-template-columns: minmax(0, 1fr) !important;
  }

  :deep([data-slot='condition-leaf']) {
    grid-column: span 1 !important;
    grid-template-columns: minmax(0, 1fr) !important;
  }

  /* The cell centres its word for a row that sits beside it; stacked, it leads. */
  :deep([data-slot='condition-group'] li > :first-child > div) {
    justify-content: flex-start;
  }

  :deep([data-slot='condition-field'] button) {
    width: 100%;
    max-width: 100%;
  }

  :deep([data-slot='condition-actions']) {
    position: absolute;
    right: -0.25rem;
    top: -0.25rem;
  }
}
</style>
