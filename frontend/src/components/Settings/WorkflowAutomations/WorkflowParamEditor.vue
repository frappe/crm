<template>
  <div class="space-y-4">
    <template v-for="field in schemaFields" :key="field.fieldname">
      <Link
        v-if="field.fieldtype === 'Link'"
        :model-value="params[field.fieldname]"
        :doctype="field.options"
        :label="field.label"
        @update:model-value="setParam(field.fieldname, $event)"
      />
      <FormControl
        v-else-if="field.fieldtype === 'Select'"
        :model-value="params[field.fieldname]"
        type="select"
        :label="field.label"
        :options="optionsFor(field)"
        @update:model-value="setParam(field.fieldname, $event)"
      />
      <FormControl
        v-else
        :model-value="valueFor(field)"
        :type="controlType(field)"
        :label="field.label"
        @update:model-value="
          setParam(field.fieldname, castValue(field, $event))
        "
      />
    </template>
  </div>
</template>

<script setup>
import Link from '@/components/Controls/Link.vue'
import { FormControl } from 'frappe-ui'
import { computed } from 'vue'

const props = defineProps({
  action: { type: Object, required: true },
  schema: { type: Object, default: null },
  doctype: { type: String, default: '' },
  fields: { type: Array, default: () => [] },
})

const schemaFields = computed(() => props.schema?.params_schema || [])

const params = computed(() => {
  try {
    return JSON.parse(props.action.params || '{}')
  } catch {
    return {}
  }
})

function optionsFor(field) {
  if (field.options_source === 'doc_fields') return docFieldOptions.value
  return String(field.options || '')
    .split('\n')
    .filter(Boolean)
}

const docFieldOptions = computed(() => {
  return props.fields.map((field) => ({
    label: field.label || field.fieldname,
    value: field.fieldname,
  }))
})

function valueFor(field) {
  const value = params.value[field.fieldname]
  if (field.fieldtype === 'JSON' && value && typeof value === 'object') {
    return JSON.stringify(value, null, 2)
  }
  return Array.isArray(value) ? value.join(', ') : value
}

function controlType(field) {
  if (['JSON', 'Text Editor'].includes(field.fieldtype)) return 'textarea'
  if (['Int', 'Float', 'Currency', 'Percent'].includes(field.fieldtype))
    return 'number'
  return 'text'
}

function castValue(field, value) {
  if (field.fieldtype === 'JSON') return castJsonField(value)
  if (controlType(field) === 'number')
    return value === '' ? null : Number(value)
  return value
}

function castJsonField(value) {
  if (!value) return []
  try {
    return JSON.parse(value)
  } catch {
    return String(value)
      .split(',')
      .map((item) => item.trim())
      .filter(Boolean)
  }
}

function setParam(fieldname, value) {
  props.action.params = JSON.stringify(
    { ...params.value, [fieldname]: value },
    null,
    2,
  )
}
</script>
