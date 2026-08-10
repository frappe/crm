<template>
  <div class="space-y-3 rounded border border-outline-gray-2 p-3">
    <div class="flex items-center justify-between">
      <div class="text-sm text-ink-gray-5">
        {{ __('Related Record Condition') }}
      </div>
      <Button
        v-if="condition"
        icon="lucide-x"
        variant="ghost"
        size="sm"
        :aria-label="__('Clear condition')"
        @click="commit(null)"
      />
    </div>
    <Button
      v-if="!condition"
      size="sm"
      icon-left="lucide-plus"
      :label="__('Add condition')"
      @click="commit(defaultCondition())"
    />
    <template v-else>
      <FormControl
        :model-value="condition.type"
        type="select"
        :label="__('Check')"
        :options="operatorOptions"
        @update:model-value="update('type', $event)"
      />
      <FormControl
        :model-value="condition.source"
        type="select"
        :label="__('Of record')"
        :options="sourceOptions"
        @update:model-value="update('source', $event)"
      />
      <FormControl
        :model-value="condition.relationship"
        type="select"
        :label="__('Related')"
        :options="relationshipOptions"
        @update:model-value="update('relationship', $event)"
      />
      <div v-if="condition.type === 'RelatedCount'" class="flex gap-2">
        <FormControl
          :model-value="condition.comparison"
          type="select"
          class="w-24"
          :label="__('Is')"
          :options="['=', '!=', '>', '>=', '<', '<=']"
          @update:model-value="update('comparison', $event)"
        />
        <FormControl
          :model-value="condition.value"
          type="number"
          class="flex-1"
          :label="__('Count')"
          @update:model-value="update('value', Number($event))"
        />
      </div>
      <FormControl
        :model-value="filtersText"
        type="textarea"
        :label="__('Filters')"
        :placeholder="`[[&quot;sent_or_received&quot;, &quot;=&quot;, &quot;Received&quot;]]`"
        @update:model-value="updateFilters($event)"
      />
      <div class="text-xs text-ink-gray-5">{{ jinjaHint }}</div>
    </template>
  </div>
</template>

<script setup>
import { capabilitiesFor } from './workflowCapabilities'
import { Button, FormControl } from 'frappe-ui'
import { computed } from 'vue'

const props = defineProps({
  modelValue: { type: String, default: '' },
  targets: { type: Array, default: () => [] },
})

const emit = defineEmits(['update:modelValue'])

const jinjaHint = `${__('Filter values may use Jinja, e.g.')} {{ trigger.creation }}`

const operatorOptions = [
  { label: __('A related record exists'), value: 'RelatedExists' },
  { label: __('No related record exists'), value: 'RelatedNotExists' },
  { label: __('Count of related records'), value: 'RelatedCount' },
]

const condition = computed(() => {
  if (!props.modelValue) return null
  try {
    return JSON.parse(props.modelValue)
  } catch {
    return null
  }
})

const sourceOptions = computed(() =>
  props.targets.map((target) => ({
    label: target.doctype
      ? `${target.alias} (${target.doctype})`
      : target.alias,
    value: target.alias,
  })),
)

const sourceDoctype = computed(
  () =>
    props.targets.find((target) => target.alias === condition.value?.source)
      ?.doctype,
)

const relationshipOptions = computed(() =>
  (capabilitiesFor(sourceDoctype.value)?.relationships || []).map(
    (definition) => ({
      label: definition.label || definition.name,
      value: definition.name,
    }),
  ),
)

const filtersText = computed(() =>
  JSON.stringify(condition.value?.filters || [], null, 2),
)

function defaultCondition() {
  return {
    type: 'RelatedExists',
    source: props.targets[0]?.alias || 'trigger',
    relationship: '',
    filters: [],
    comparison: '>=',
    value: 1,
  }
}

function update(key, value) {
  commit({ ...condition.value, [key]: value })
}

function updateFilters(text) {
  try {
    update('filters', JSON.parse(text || '[]'))
  } catch {
    // keep the last valid filters until the JSON parses again
  }
}

function commit(next) {
  emit('update:modelValue', next ? JSON.stringify(next) : '')
}
</script>
