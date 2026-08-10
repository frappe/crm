<template>
  <div class="space-y-2">
    <label v-if="label" class="block text-sm text-ink-gray-5">{{
      label
    }}</label>
    <div
      v-for="(filter, index) in filters"
      :key="index"
      class="flex min-w-0 gap-2"
    >
      <Autocomplete
        class="min-w-0 flex-1"
        :model-value="fieldOption(filter[0])"
        :options="fieldOptions"
        :placeholder="__('Field')"
        @update:model-value="setField(index, $event)"
      />
      <Combobox
        class="w-28 shrink-0"
        :model-value="filter[1]"
        :options="operatorOptions(filter[0])"
        :placeholder="__('Operator')"
        @update:model-value="setValue(index, 1, $event)"
      />
      <Combobox
        v-if="choiceOptions(filter).length"
        class="min-w-0 flex-1"
        :model-value="filter[2]"
        :options="choiceOptions(filter)"
        :placeholder="__('Value')"
        @update:model-value="setValue(index, 2, $event)"
      />
      <FormControl
        v-else
        class="min-w-0 flex-1"
        :model-value="displayValue(filter)"
        :placeholder="__('Value')"
        @update:model-value="setFilterValue(index, $event)"
      />
      <Button
        class="shrink-0"
        icon="lucide-x"
        variant="ghost"
        :aria-label="__('Remove filter')"
        @click="removeFilter(index)"
      />
    </div>
    <Button
      :label="__('Add Filter')"
      icon-left="lucide-plus"
      variant="ghost"
      @click="addFilter"
    />
  </div>
</template>

<script setup>
import { Autocomplete, Button, Combobox, FormControl } from 'frappe-ui'
import { computed } from 'vue'

const props = defineProps({
  modelValue: { type: [String, Array], default: '' },
  fields: { type: Array, default: () => [] },
  label: { type: String, default: () => __('Filters') },
})

const emit = defineEmits(['update:modelValue'])

const filters = computed(() => parseFilters(props.modelValue))
const fieldOptions = computed(() => props.fields.map(toFieldOption))

function parseFilters(value) {
  if (Array.isArray(value)) return value
  try {
    const parsed = JSON.parse(value || '[]')
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return []
  }
}

function toFieldOption(field) {
  return { label: field.label || field.fieldname, value: field.fieldname }
}

function fieldOption(fieldname) {
  return fieldOptions.value.find((option) => option.value === fieldname) || null
}

function selectedField(fieldname) {
  return props.fields.find((field) => field.fieldname === fieldname)
}

function operatorOptions(fieldname) {
  const common = ['=', '!=', 'in', 'not in', 'is']
  const comparisons = ['>', '>=', '<', '<=']
  const fieldtype = selectedField(fieldname)?.fieldtype
  return ['Int', 'Float', 'Currency', 'Percent', 'Date', 'Datetime'].includes(
    fieldtype,
  )
    ? [...common, ...comparisons]
    : [...common, 'like', 'not like']
}

function choiceOptions(filter) {
  if (filter[1] === 'is') return ['set', 'not set']
  if (['in', 'not in'].includes(filter[1])) return []
  const field = selectedField(filter[0])
  if (field?.fieldtype === 'Check')
    return [
      { label: __('Yes'), value: 1 },
      { label: __('No'), value: 0 },
    ]
  if (field?.fieldtype !== 'Select') return []
  return String(field.options || '')
    .split('\n')
    .filter(Boolean)
}

function displayValue(filter) {
  return Array.isArray(filter[2]) ? filter[2].join(', ') : filter[2]
}

function setField(index, option) {
  const next = cloneFilters()
  next[index] = [option?.value || '', '=', '']
  commit(next)
}

function setValue(index, position, value) {
  const next = cloneFilters()
  next[index][position] = value
  commit(next)
}

function setFilterValue(index, value) {
  const operator = filters.value[index][1]
  setValue(
    index,
    2,
    ['in', 'not in'].includes(operator) ? splitValues(value) : value,
  )
}

function splitValues(value) {
  return String(value || '')
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean)
}

function addFilter() {
  commit([...cloneFilters(), ['', '=', '']])
}

function removeFilter(index) {
  const next = cloneFilters()
  next.splice(index, 1)
  commit(next)
}

function cloneFilters() {
  return filters.value.map((filter) => [...filter])
}

function commit(next) {
  emit('update:modelValue', next.length ? JSON.stringify(next) : '')
}
</script>
