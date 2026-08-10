<template>
  <div class="space-y-3">
    <div class="flex items-center justify-between">
      <div class="text-sm text-ink-gray-5">{{ __('Related Records') }}</div>
      <Button
        icon-left="lucide-plus"
        size="sm"
        :label="__('Alias')"
        @click="addAlias"
      />
    </div>
    <div v-if="!aliases.length" class="text-xs text-ink-gray-5">
      {{
        __(
          'Name a linked record here to use it as an action target or condition source.',
        )
      }}
    </div>
    <div
      v-for="(item, index) in aliases"
      :key="index"
      class="space-y-2 rounded border border-outline-gray-2 p-3"
    >
      <div class="flex items-center gap-2">
        <FormControl
          :model-value="item.alias"
          class="flex-1"
          :placeholder="__('alias, e.g. lead')"
          @update:model-value="update(index, 'alias', $event)"
        />
        <Button
          icon="lucide-trash-2"
          variant="ghost"
          :aria-label="__('Remove alias')"
          @click="removeAlias(index)"
        />
      </div>
      <FormControl
        :model-value="item.source || 'trigger'"
        type="select"
        :label="__('From')"
        :options="sourceOptions(index)"
        @update:model-value="update(index, 'source', $event)"
      />
      <FormControl
        :model-value="item.relationship"
        type="select"
        :label="__('Relationship')"
        :options="relationshipOptions(item, index)"
        @update:model-value="update(index, 'relationship', $event)"
      />
    </div>
  </div>
</template>

<script setup>
import { aliasTargets, capabilitiesFor } from './workflowCapabilities'
import { Button, FormControl } from 'frappe-ui'
import { computed } from 'vue'

const props = defineProps({
  modelValue: { type: String, default: '[]' },
  documentType: { type: String, default: '' },
})

const emit = defineEmits(['update:modelValue'])

const aliases = computed(() => {
  try {
    return JSON.parse(props.modelValue || '[]')
  } catch {
    return []
  }
})

/** Aliases declared before this row, so a relationship can hang off an earlier one. */
function targetsBefore(index) {
  return aliasTargets(props.documentType, aliases.value.slice(0, index))
}

function sourceOptions(index) {
  return targetsBefore(index).map((target) => ({
    label: target.doctype
      ? `${target.alias} — ${target.doctype}`
      : target.alias,
    value: target.alias,
  }))
}

/** Only single-record relationships can become an alias; `many` ones drive conditions. */
function relationshipOptions(item, index) {
  const source = targetsBefore(index).find(
    (target) => target.alias === (item.source || 'trigger'),
  )
  return (capabilitiesFor(source?.doctype)?.relationships || [])
    .filter((definition) => definition.cardinality === 'one')
    .map((definition) => ({
      label: definition.label || definition.name,
      value: definition.name,
    }))
}

function addAlias() {
  commit([...aliases.value, { alias: '', source: 'trigger', relationship: '' }])
}

function removeAlias(index) {
  commit(aliases.value.filter((_, position) => position !== index))
}

function update(index, key, value) {
  commit(
    aliases.value.map((item, position) =>
      position === index ? { ...item, [key]: value } : item,
    ),
  )
}

function commit(next) {
  emit('update:modelValue', JSON.stringify(next))
}
</script>
