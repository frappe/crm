<template>
  <div class="space-y-2">
    <div class="flex items-center gap-1">
      <label class="block text-sm text-ink-gray-5">
        {{ __('Related Records') }}
      </label>
      <Tooltip
        :text="
          __('Name a record linked to the trigger so steps can act on it.')
        "
      >
        <InfoIcon class="size-3.5 text-ink-gray-5" />
      </Tooltip>
    </div>
    <div
      v-for="(item, index) in items"
      :key="index"
      class="space-y-2 rounded-lg border border-outline-gray-2 p-3"
    >
      <div class="flex items-center gap-2">
        <FormControl
          class="flex-1"
          type="select"
          variant="outline"
          :model-value="item.relationship"
          :options="relationshipOptions"
          :placeholder="__('Relationship')"
          :aria-label="__('Relationship')"
          @update:model-value="setRelationship(index, $event)"
        />
        <Button
          variant="ghost"
          icon="lucide-trash-2"
          :aria-label="__('Remove related record')"
          @click="remove(index)"
        />
      </div>
      <FormControl
        v-if="choicesFor(item).length > 1"
        type="select"
        variant="outline"
        :model-value="item.target_doctype"
        :options="choicesFor(item)"
        :placeholder="__('DocType')"
        :aria-label="__('DocType')"
        @update:model-value="patch(index, { target_doctype: $event })"
      />
      <FormControl
        variant="outline"
        :model-value="item.alias"
        :placeholder="__('Alias')"
        :aria-label="__('Alias')"
        @update:model-value="patch(index, { alias: $event })"
      />
    </div>
    <div class="flex w-full rounded-lg border border-outline-gray-2 p-3">
      <Button
        :label="__('Add Related Record')"
        icon-left="lucide-plus"
        :disabled="!relationshipOptions.length"
        @click="add"
      />
    </div>
  </div>
</template>

<script setup>
import { capabilitiesFor } from './workflowCapabilities'
import InfoIcon from '~icons/lucide/info'
import { Button, FormControl, Tooltip } from 'frappe-ui'
import { computed } from 'vue'

const props = defineProps({
  modelValue: { type: [String, Array], default: '[]' },
  doctype: { type: String, default: '' },
})

const emit = defineEmits(['update:modelValue'])

const items = computed(() => read(props.modelValue))

// Only a single record can back an alias.
const definitions = computed(() =>
  (capabilitiesFor(props.doctype)?.relationships || []).filter(
    (definition) => definition.cardinality === 'one',
  ),
)

const relationshipOptions = computed(() =>
  definitions.value.map((definition) => ({
    label: definition.label || definition.name,
    value: definition.name,
  })),
)

function read(value) {
  if (Array.isArray(value)) return value
  try {
    const parsed = JSON.parse(value || '[]')
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return []
  }
}

function choicesFor(item) {
  const definition = definitions.value.find(
    (entry) => entry.name === item.relationship,
  )
  return definition?.target_doctypes || []
}

function store(next) {
  emit('update:modelValue', JSON.stringify(next))
}

function patch(index, values) {
  store(
    items.value.map((item, i) => (i === index ? { ...item, ...values } : item)),
  )
}

function setRelationship(index, relationship) {
  const item = items.value[index]
  patch(index, {
    relationship,
    target_doctype: '',
    alias: item.alias || relationship,
  })
}

function add() {
  store([...items.value, { alias: '', source: 'trigger', relationship: '' }])
}

function remove(index) {
  store(items.value.filter((_, i) => i !== index))
}
</script>
